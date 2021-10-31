import asyncio
import click
from jinja2 import Template
from .database import Participant, MiniexamResponseType, MiniexamResponseLanguage, MiniexamResponse
from .utils import get_session
from itertools import zip_longest
from quart import url_for
from .app import app


EMAIL_TEMPLATE = Template("""
To: {{ email }}
Subject: Lost responses in Finnish vocabulary study mini-exam
---
Dear {{ full_name }},

Thank you very much for completing the study. Unfortunately, due to a bug in
the website, some of the responses from the mini-exam were lost. I was able to
partially retrieve your responses, but some are missing. Could you please
follow the link below and re-enter the missing information to the best of your
ability? Please only fill in the missing information.

I truly am very sorry for the inconvience.

{{ link }}

I will be in contact with the University about processing your payment shortly.

Best regards,

Frankie Robertson
Doctoral Researcher in Educational Technology
Faculty of Information Technology
University of Jyväskylä
""".strip())


@click.command()
@click.argument("email", nargs=-1)
def main(email):
    session = get_session()
    loop = asyncio.get_event_loop()

    async def get_link():
        async with app.app_context():
            return url_for(
                "fixup_miniexam",
                _external=True,
                _scheme="https" if not app.debug else "http"
            )
    link = loop.run_until_complete(get_link())
    for em in email:
        participant = session.query(Participant).filter_by(email=em).first()
        cols = {"slot": [], "slot_order": [], "lang": [], "type": [], "response": []}
        empty_start = None
        for idx, miniexam_slot in enumerate(participant.miniexam_slots):
            cols["slot"].append(miniexam_slot)
            cols["slot_order"].append(miniexam_slot.miniexam_order)
            if miniexam_slot.responses:
                resp = miniexam_slot.responses[-1]
                cols["type"].append(resp.response_type)
                lang = resp.response_lang
                if lang is None and resp.response_type != MiniexamResponseType.donotknow:
                    lang = MiniexamResponseLanguage.fi
                cols["lang"].append(lang)
                if resp.response_type == MiniexamResponseType.donotknow:
                    cols["response"].insert(idx, "")
                cols["response"].append(resp.response)
            elif empty_start is None:
                empty_start = idx
        cols["response"] = cols["response"][:empty_start]
        slots_grouped = {}
        for slot_order, slot in zip(cols["slot_order"], cols["slot"]):
            slots_grouped.setdefault(slot_order, []).append(slot)
        active_slots = set()
        deleted = 0
        for slots in slots_grouped.values():
            for slot in slots[:-1]:
                session.delete(slot)
                deleted += 1
            active_slots.add(slots[-1].id)
        if deleted:
            print(f"Deleted {deleted} slots")
        for slot in participant.miniexam_slots:
            for resp in slot.responses:
                session.delete(resp)
        for slot, lang, type, resp in \
                zip_longest(
                    cols["slot"],
                    cols["lang"],
                    cols["type"],
                    cols["response"]
                ):
            if slot.id not in active_slots:
                continue
            session.add(MiniexamResponse(
                slot=slot,
                timestamp=None,
                response_type=type,
                response_lang=lang,
                response=resp or "",
            ))
        session.commit()

        print(EMAIL_TEMPLATE.render(
            email=participant.email,
            full_name=f"{participant.given_name} {participant.surname}",
            link=link + "?token=" + participant.token,
        ))


if __name__ == "__main__":
    main()
