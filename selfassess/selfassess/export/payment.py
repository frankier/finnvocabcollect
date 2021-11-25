import click
from pandas import DataFrame

from selfassess.utils import get_session
from selfassess.database import Participant
from selfassess.queries import participant_timeline_query
from .utils import get_participant_sessions


@click.command()
@click.argument("csvout", type=click.Path())
@click.argument("include_email", nargs=-1)
def main(csvout, include_email):
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
    period_start = []
    period_end = []
    for participant in participants:
        if include_email and participant.email not in include_email:
            continue
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
        period_start.append(participant.accept_date.date().isoformat())
        period_end.append(participant.miniexam_finish_date.date().isoformat())
    df = DataFrame({
        "name": names,
        "surname": surnames,
        "email": email,
        "period start": period_start,
        "period end": period_end,
        "amount (€)": "200",
    })
    df.to_csv(csvout, sep='\t')


if __name__ == "__main__":
    main()
