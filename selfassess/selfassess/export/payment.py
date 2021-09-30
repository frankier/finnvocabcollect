import click
from pandas import DataFrame

from selfassess.utils import get_session
from selfassess.database import Participant
from .utils import get_participant_sessions
from .queries import participant_timeline_query


@click.command()
@click.argument("csvout", type=click.Path())
def main(csvout):
    """
    Given name

    Surname

    E-mail address

    Period of the task to be done
    """
    sqlite_sess = get_session()
    participants = sqlite_sess.execute(participant_timeline_query()).scalars()
    names = []
    surnames = []
    email = []
    period = []
    for participant in participants:
        names.append(participant.given_name)
        surnames.append(participant.surname)
        email.append(participant.email)
        time = (
            sum((
                part_session["time"].total_seconds()
                for part_session
                in get_participant_sessions(participant)
            ))
        ) / (60 * 60)
        period.append(int(time * 4 + 0.5) / 4)
    df = DataFrame({
        "name": names,
        "surname": surnames,
        "email": email,
        "period": period,
    })
    df.to_csv(csvout, float_format='%.2f')


if __name__ == "__main__":
    main()
