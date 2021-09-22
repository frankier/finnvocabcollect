import click

from .database import Participant
from .utils import get_session


@click.command()
@click.argument("email")
def main(email):
    session = get_session()
    participant = (
        session.query(Participant).filter(email=email).scalars().first()
    )
    for miniexam_slot in participant.miniexam_slots:
        resp = miniexam_slot.responses[-1]
        while 1:
            mark = input("Word: {}; Language: {}; Type: {}; Response: {} (1-5) > ".format(
                miniexam_slot.word.word,
                resp.response_lang.name(),
                resp.response_type.name(),
                resp.response
            ))
            mark = int(mark)
            if mark in range(1, 6):
                resp.mark = mark
                session.commit()
                break


if __name__ == "__main__":
    main()
