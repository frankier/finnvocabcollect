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
        # Moved to selfassess.mark
        #"miniexam_accept",
        "withdraw"
    ])
)
@click.argument("email")
def main(action, email):
    session = get_session()
    participant = session.execute(
        session.query(Participant).filter_by(email=email)
    ).scalars().first()
    setattr(
        participant,
        f"{action}_date",
        datetime.datetime.now()
    )
    session.add(participant)
    session.commit()


if __name__ == "__main__":
    main()
