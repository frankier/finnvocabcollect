import click
import shortuuid
from .utils import get_session
from jinja2 import Template
from quart import url_for
import datetime
from .database import (
    Participant, ParticipantLanguage, Word, ResponseSlot, ProofAge, ProofType
)
from .app import app
import asyncio
from sqlalchemy import select
import random
import langcodes
from .quali import CEFR_LEVELS, CEFR_SKILLS


EMAIL_TEMPLATE = Template("""
Your participation in self-assessed Finnish vocabulary study / Osallistumisesi itsearvioituun suomen sanaston tutkimukseen
---

(English below.) Tämä sähköposti ja verkkosivusto ovat saatavilla vain
englanniksi, koska kaikki osallistujat vastasivat ymmärtävänsä englantia. Jos
sinulla on vaikeuksia ymmärtää tutkimusta, voit aina saada apua vastaamalla
tähän sähköpostiin valitsemallasi kielellä.

/ / /

Dear prospective participant,

Thanks for your interest in our study. We can confirm we would like you to
participate in our study of vocabulary in learners of the Finnish language.
This website gives the full details of the study:

{{ link }}

The above link is a personal login to and access the study website. Please keep
this email so you can continue to access the study website. Please do not share
the above link with others.

You can find further details about the study and confirm your participation
using the website. If you want to participate, please do so and begin the
self-assessment within 7 days (by {{ accept_deadline }}) or we will assume you
no longer wish to participate in the study and remove you. You must complete
the whole study within 21 days (by {{ complete_deadline }}).

If you already know that you do not want to participate, please let me know by
replying to this email and you will be withdrawn and your information expunged.

Best regards,

Frankie Robertson
Doctoral Researcher in Educational Technology
Faculty of Information Technology
University of Jyväskylä
""".strip())


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
    while 1:
        proof_type = input(
            "Proof type (yki_intermediate/yki_advanced/other) > "
        )
        if proof_type in ProofType.__members__:
            proof_type = ProofType[proof_type]
            break
    while 1:
        proof_age = input(
            "Proof age (lt1/lt3/lt5/gte5) > "
        )
        if proof_age in ProofAge.__members__:
            proof_age = ProofAge[proof_age]
            break
    text_on_proof = []
    while 1:
        inp = input("Text on proof > ")
        if inp == "":
            text_on_proof = "\n".join(text_on_proof)
            break
        text_on_proof.append(inp)
    cefrs = []
    for type in ("proof", "selfassess"):
        for skill in CEFR_SKILLS:
            while 1:
                level = input(f"{type} {skill} > ")
                if level in CEFR_LEVELS:
                    level = CEFR_LEVELS.index(level) + 1
                else:
                    level = int(level)
                    if level < 1 or level > 6:
                        continue
                break
            cefrs.append((type, skill, level))
    print()
    print("Email:", email)
    print("Native language:", native_lang_obj.display_name())
    for other_lang, cefr in other_langs:
        print("Other language:", other_lang.display_name(), cefr)
    print("Proof type:", proof_type.name)
    print("Proof age:", proof_age.name)
    print("Text on proof:")
    print(text_on_proof)
    for type, skill, level in cefrs:
        print(type.title(), skill.title() + ":", "{}/{}".format(CEFR_LEVELS[level - 1].upper(), level))
    print()
    while 1:
        resp = input("Confirm? (y/n) > ").strip().lower()
        if resp == "n":
            print("Exiting. Rerun with correct values.")
            return
        elif resp == "y":
            print("Inserting")
            break
    return native_lang_obj, other_langs, proof_type, proof_age, text_on_proof, cefrs


@click.command()
@click.argument("email")
def main(email):
    native_lang, other_langs, proof_type, proof_age, text_on_proof, cefrs = prompts(email)
    session = get_session()
    token = shortuuid.uuid()
    create_datetime = datetime.datetime.now()
    accept_deadline = (
        create_datetime + datetime.timedelta(weeks=1)
    ).date()
    complete_deadline = (
        create_datetime + datetime.timedelta(weeks=3)
    ).date()
    with session.begin():
        participant = Participant(
            token=token,
            create_date=create_datetime,
            accept_date=None,
            email=email,
            accept_deadline=accept_deadline,
            complete_deadline=complete_deadline,
            proof_type=proof_type,
            proof_age=proof_age,
            text_on_proof=text_on_proof,
            **{
                f"cefr_{type}_{skill}": level
                for type, skill, level in cefrs
            }
        )
        session.add(participant)
        participant_language = ParticipantLanguage(
            participant=participant,
            language=native_lang.language,
            level="native",
        )
        session.add(participant_language)
        for other_lang, cefr in other_langs:
            participant_language = ParticipantLanguage(
                participant=participant,
                language=other_lang.language,
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
    print(EMAIL_TEMPLATE.render(
        link=link,
        accept_deadline=accept_deadline.strftime('%A %d/%m/%Y'),
        complete_deadline=complete_deadline.strftime('%A %d/%m/%Y'),
    ))


if __name__ == "__main__":
    main()
