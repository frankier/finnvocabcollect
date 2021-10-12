import click
from pandas import DataFrame

from selfassess.export.utils import get_participant_sessions
from selfassess.queries import participant_timeline_query
from selfassess.utils import get_session


@click.command()
@click.argument("dfout")
def main(dfout):
    sqlite_sess = get_session()
    participants = sqlite_sess.execute(participant_timeline_query()).scalars()
    pids = []
    sids = []
    times = []
    for participant in participants:
        selfassess_sessions = get_participant_sessions(
            participant,
            only_selfassess=True
        )
        for sid, session in enumerate(selfassess_sessions):
            for response in session["response"]:
                pids.append(participant.id)
                sids.append(sid)
                times.append(response.timestamp)
    df = DataFrame({
        "pids": pids,
        "sids": sids,
        "times": times,
    })
    df.to_parquet(dfout)


if __name__ == "__main__":
    main()
