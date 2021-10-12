import click
import pandas
import numpy as np
import matplotlib.pyplot as plt
from os.path import join as pjoin
from os import makedirs

from freqknowfit.nonparametric.transfer import draw_plot
from finnwordlist.multicorpusfreqs import REL_FREQ_COLS
from finnwordlist.aggs import AGG_COLS

COLS = [
    *AGG_COLS,
    *REL_FREQ_COLS
]


def plot(df, out_fn, bw):
    fig, axs = plt.subplots(3, 3, sharex=True, sharey=True)
    fig.set_size_inches(12, 12)
    for ax, col in zip(axs.flatten(), COLS):
        df["zipf"] = np.log10(df[col] * 1000)
        try:
            draw_plot(df, ax, create_fit=False, ordinal=True, bw=bw)
        except ValueError:
            ax.set_facecolor('xkcd:salmon')
    plt.tight_layout()
    fig.savefig(out_fn)


@click.command()
@click.argument("wordlist_inf", type=click.File("rb"))
@click.argument("know_inf", type=click.File("rb"))
@click.argument("figout")
@click.option("--split-sessions/--plot-per-participant")
@click.option("--bw", default=0.08, type=float)
def main(wordlist_inf, know_inf, figout, split_sessions, bw):
    wordlist_df = pandas.read_parquet(wordlist_inf)
    know_df = pandas.read_csv(know_inf)
    know_df["score"] = know_df["rating"]
    know_df = know_df.join(wordlist_df.set_index("lemma"), "word")
    makedirs(figout, exist_ok=True)
    for participant, group_df in know_df.groupby("participant"):
        # TODO: modify freqknowfit to take column names
        if split_sessions:
            participant_dir = pjoin(figout, str(participant))
            makedirs(participant_dir, exist_ok=True)
            plot(group_df, pjoin(participant_dir, "all.png"), bw=bw)
            for session, session_df in group_df.groupby("session_id"):
                out_fn = pjoin(participant_dir, f"{session}.png")
                plot(session_df, out_fn, bw=bw)
        else:
            plot(group_df, pjoin(figout, f"{participant}.png"), bw=bw)


if __name__ == "__main__":
    main()
