import click

from .new import get_proof_type
from .database import Participant
from .utils import get_session


@click.command()
@click.argument("email")
def main(email):
    session = get_session()
    participant = session.execute(
        session.query(Participant).filter_by(email=email)
    ).scalars().first()
    print("Currently", participant.proof_type)
    proof_type = get_proof_type()
    participant.proof_type = proof_type


if __name__ == "__main__":
    main()
