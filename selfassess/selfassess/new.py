import click
import shortuuid
from .utils import get_session
from jinja2 import Template
from quart import url_for
import datetime
from .database import Participant, Word, ResponseSlot
from .app import app
import asyncio
from sqlalchemy import select
import random


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


@click.command()
@click.argument("email")
def main(email):
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
