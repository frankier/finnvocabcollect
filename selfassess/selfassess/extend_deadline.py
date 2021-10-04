import click
from datetime import timedelta

from .database import Participant
from .utils import get_session


@click.command()
@click.option("--days", type=int, default=1)
@click.argument("email", nargs=-1)
def main(days, email):
    session = get_session()
    participants = session.execute(
        session.query(Participant).filter(Participant.email.in_(email))
    ).scalars()
    for participant in participants:
        participant.complete_deadline += timedelta(days=days)
        session.add(participant)
    session.commit()


if __name__ == "__main__":
    main()
