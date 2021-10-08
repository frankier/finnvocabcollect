import click
from os import remove
from os.path import join as pjoin

from .app import app
from .database import Participant
from .utils import get_session


@click.command()
def main():
    session = get_session()
    participants = session.execute(
        session.query(Participant)
        .filter(Participant.selfassess_accept_date.isnot(None))
    ).scalars()
    for participant in participants:
        path = pjoin(app.config['UPLOAD_DIR'], participant.proof)
        while 1:
            resp = input(f"Remove {path}? y/n")
            if resp == "y":
                break
            elif resp == "n":
                print("Aborting")
                return
        remove(path)


if __name__ == "__main__":
    main()
