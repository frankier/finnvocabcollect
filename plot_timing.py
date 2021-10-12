import click
from more_itertools import windowed
import matplotlib.pyplot as plt
from os import makedirs
from os.path import join as pjoin
from pandas import read_parquet


def plot(responses, out_fn, window):
    intervals = []
    fig, ax = plt.subplots()
    for responses in windowed(responses, window):
        if responses[-1] is None or responses[0] is None:
            continue
        interval = (
            (responses[-1] - responses[0]).total_seconds() /
            (window - 1)
        )
        intervals.append(interval)
        plt.tight_layout()
    ax.scatter(x=range(len(intervals)), y=intervals)
    plt.tight_layout()
    fig.savefig(out_fn)
    plt.close(fig)


@click.command()
@click.argument("dfin")
@click.argument("figout")
@click.option("--window", type=int, default=5)
def main(dfin, figout, window):
    df = read_parquet(dfin)
    for participant_id, participant_df in df.groupby("pids"):
        participant_dir = pjoin(figout, str(participant_id))
        makedirs(participant_dir, exist_ok=True)
        for session_id, session_df in participant_df.groupby("sids"):
            out_fn = pjoin(participant_dir, f"{session_id}.png")
            plot(
                session_df["times"],
                out_fn,
                window
            )
            interval = (
                (session_df["times"][-1] - session_df["times"][0]) /
                (len(session_df["times"]) - 1)
            )
            print(
                f"Participant {participant_id}; Session {session_id}: {interval:02d}"
            )


if __name__ == "__main__":
    main()
