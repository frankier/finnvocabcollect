import click
import datetime

from .database import Participant
from .utils import get_session


@click.command()
@click.argument(
    "action",
    type=click.Choice([
        "proof_accept",
        "selfassess_accept",
        "miniexam_accept",
        "withdraw"
    ])
)
@click.argument("email")
def main(stage, email):
    session = get_session()
    participant = (
        session.query(Participant).filter(email=email).scalars().first()
    )
    setattr(
        participant,
        f"{stage}_date",
        datetime.datetime.now()
    )
    session.add(participant)
    session.commit()


if __name__ == "__main__":
    main()
