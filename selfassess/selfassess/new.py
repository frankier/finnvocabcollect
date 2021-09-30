import click
import traceback
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
from .quali import CEFR_LEVELS_NATIVE, CEFR_SKILLS
from functools import partial


EMAIL_TEMPLATE = Template("""
To: {{ email }}
Subject: Your participation in self-assessed Finnish vocabulary study / Osallistumisesi itsearvioituun suomen sanaston tutkimukseen
---

(English below.) Koska kaikki osallistujat vastasivat ymmärtävänsä englantia,
tämä sähköposti ja tutkimuksen verkkosivusto ovat saatavilla vain englanniksi.
Jos sinulla on vaikeuksia ymmärtää kyselyä, voit pyytää ohjeita vastaamalla
tähän sähköpostiin haluamallasi kielellä.

/ / /

Dear prospective participant,

Thank you for your interest in our study. We can confirm we would like you to
participate in our study of vocabulary in learners of the Finnish language.
This website gives the full details:

{{ link }}

The above link is a personal login to and access the study website. Please keep
this email so you can continue to access the study website. Please do not share
the above link with others.

You can find further details about the study and confirm your participation
using the website. If you want to participate, please do so and begin the
self-assessment within {{ begin_days }} days (by {{ accept_deadline }}) or we
will assume you no longer wish to participate in the study and remove you. You
must complete the whole study within 21 days (by {{ complete_deadline }}).

If you already know that you do not want to participate, please let me know by
replying to this email and you will be withdrawn and your information expunged.

You can also reply to this email if you encounter any problems completing the
study.

Best regards,

Frankie Robertson
Doctoral Researcher in Educational Technology
Faculty of Information Technology
University of Jyväskylä
""".strip())


def convert_cefr(level, max_level=7, allow_none=False):
    level = level.strip()
    if allow_none and level == "none":
        return None
    if level in CEFR_LEVELS_NATIVE:
        level = CEFR_LEVELS_NATIVE.index(level) + 1
    else:
        level = int(level)
    if level < 1 or level > max_level:
        raise ValueError(f"Level {level} out of range 1-{max_level}")
    return level


def convert_opt_lang(lang):
    lang = lang.strip().lower()
    if not lang:
        return
    return langcodes.get(lang)


def convert_lang(lang):
    return langcodes.get(lang.strip().lower())


def repeat_input(prompt, process):
    while 1:
        result = input(prompt + " > ")
        try:
            proc_result = process(result)
        except Exception:
            traceback.print_exc()
        else:
            return proc_result


def enum_prompt(prompt, enum):
    return repeat_input(
        "{} ({})".format(prompt, "/".join((opt.name for opt in enum))),
        lambda k: enum[k]
    )


def get_proof_type():
    return enum_prompt("Proof type", ProofType)


def prompts(email):
    years_in_finland = repeat_input("Years in Finland", int)
    native_lang_obj = repeat_input("Native language (iso alpha2 code)", convert_lang)
    other_langs = []
    while 1:
        other_lang_obj = repeat_input(
            "Other language (iso alpha2 code or blank to finish)",
            convert_opt_lang
        )
        if not other_lang_obj:
            break
        cefr = repeat_input("CEFR level (a1-c2/native/none or 1-7)", partial(convert_cefr, allow_none=True))
        other_langs.append((other_lang_obj, cefr))
    proof_type = get_proof_type()
    proof_age = repeat_input(
        "Proof age (lt1/lt3/lt5/gte5)",
        lambda k: ProofAge[k]
    )
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
            level = repeat_input(f"{type} {skill} (a1-c2 or 1-6)", partial(convert_cefr, max_level=6))
            cefrs.append((type, skill, level))
    print()
    print("Email:", email)
    print("Years in Finland", years_in_finland)
    print("Native language:", native_lang_obj.display_name())
    for other_lang, cefr in other_langs:
        print("Other language:", other_lang.display_name(), cefr)
    print("Proof type:", proof_type.name)
    print("Proof age:", proof_age.name)
    print("Text on proof:")
    print(text_on_proof)
    for type, skill, level in cefrs:
        print(type.title(), skill.title() + ":", "{}/{}".format(CEFR_LEVELS_NATIVE[level - 1].upper(), level))
    print()
    while 1:
        resp = input("Confirm? (y/n) > ").strip().lower()
        if resp == "n":
            print("Exiting. Rerun with correct values.")
            return
        elif resp == "y":
            print("Inserting")
            break
    return years_in_finland, native_lang_obj, other_langs, proof_type, proof_age, text_on_proof, cefrs


@click.command()
@click.argument("email")
@click.option("--days", type=int, default=4)
def main(email, days):
    years_in_finland, native_lang, other_langs, proof_type, proof_age, text_on_proof, cefrs = prompts(email)
    session = get_session()
    token = shortuuid.uuid()
    create_datetime = datetime.datetime.now()
    accept_deadline = (
        create_datetime + datetime.timedelta(days=days)
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
            begin_days=days,
            accept_deadline=accept_deadline,
            complete_deadline=complete_deadline,
            proof_type=proof_type,
            proof_age=proof_age,
            text_on_proof=text_on_proof,
            lived_in_finland=years_in_finland,
            **{
                f"cefr_{type}_{skill}": level
                for type, skill, level in cefrs
            }
        )
        session.add(participant)
        participant_language = ParticipantLanguage(
            participant=participant,
            language=native_lang.language,
            level=7,
            primary_native=True
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
            return url_for(
                "start",
                token=token,
                _external=True,
                _scheme="https" if not app.debug else "http"
            )
    loop = asyncio.get_event_loop()
    link = loop.run_until_complete(get_link())
    print(EMAIL_TEMPLATE.render(
        email=email,
        link=link,
        accept_deadline=accept_deadline.strftime('%A %d/%m/%Y'),
        complete_deadline=complete_deadline.strftime('%A %d/%m/%Y'),
    ))


if __name__ == "__main__":
    main()
