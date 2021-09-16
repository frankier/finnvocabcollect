import click
import shortuuid
from .utils import get_session
from jinja2 import Template
from quart import url_for
import datetime
from .database import Participant, ParticipantLanguage, Word, ResponseSlot
from .app import app
import asyncio
from sqlalchemy import select
import random
import langcodes


EMAIL_TEMPLATE = Template("""
/ Your participation in self-assessed Finnish vocabulary study
---

(English below.) FINNISH HERE

/ / /

Dear prospective participant,

Thanks for your interest in our study. We can confirm we would like you to
participate. The website below details the various steps:

{{ link }}

The above link is your way to login to and access the study website. Please
keep this email so you can continue to access the study website.

You can find further details about the study and confirm your participation
using the website. Please do so within 10 days (by XX) or we will assume you no
longer wish to participate in the study and remove you. If you know that you do
not want to participate, please reply to this email and you will be removed and
your information expunged.
""".strip())

CEFR_LEVELS = {"a1", "a2", "b1", "b2", "c1", "c2"}


def prompts(email):
    native_lang = input("Native language (iso alpha2 code) > ")
    native_lang_obj = langcodes.get(native_lang)
    other_langs = []
    while 1:
        other_lang = input(
            "Other language (iso alpha2 code or blank to finish) > "
        ).strip().lower()
        if not other_lang:
            break
        other_lang_obj = langcodes.get(other_lang)
        while 1:
            cefr = input("CEFR level > ").strip().lower()
            if cefr not in CEFR_LEVELS:
                print(f"{cefr} not in {CEFR_LEVELS!r} -- try again!")
            else:
                break
        other_langs.append((other_lang_obj, cefr))
    print("Email:", email)
    print("Native language", native_lang_obj.display_name())
    for other_lang, cefr in other_langs:
        print("Other language", other_lang.display_name(), cefr)
    while 1:
        resp = input("Confirm? (y/n) > ").strip().lower()
        if resp == "n":
            print("Exiting. Rerun with correct values.")
            return
        elif resp == "y":
            print("Inserting")
    return native_lang_obj, other_langs


@click.command()
@click.argument("email")
def main(email):
    native_lang, other_langs = prompts(email)
    session = get_session()
    token = shortuuid.uuid()
    with session.begin():
        participant = Participant(
            token=token,
            create_date=datetime.datetime.now(),
            accept_date=None,
            email=email,
        )
        session.add(participant)
        participant_language = ParticipantLanguage(
            language=native_lang.alpha2,
            level="native",
        )
        session.add(participant_language)
        for other_lang, cefr in other_langs:
            participant_language = ParticipantLanguage(
                language=other_lang.alpha2,
                level=cefr,
            )
            session.add(participant_language)
        word_ids = [
            word_id for (word_id,) in session.execute(select(Word.id)).all()
        ]
        random.shuffle(word_ids)
        for idx, word_id in enumerate(word_ids):
            session.add(ResponseSlot(
                response_order=idx,
                participant=participant,
                word_id=word_id
            ))

    async def get_link():
        async with app.app_context():
            return url_for("start", token=token)
    loop = asyncio.get_event_loop()
    link = loop.run_until_complete(get_link())
    print(EMAIL_TEMPLATE.render(link=link))


if __name__ == "__main__":
    main()
