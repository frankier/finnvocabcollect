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


@click.command()
@click.argument("wordlist_inf", type=click.File("rb"))
@click.argument("know_inf", type=click.File("rb"))
@click.argument("figout")
def main(wordlist_inf, know_inf, figout):
    bw = 0.08
    wordlist_df = pandas.read_parquet(wordlist_inf)
    know_df = pandas.read_csv(know_inf)
    know_df["score"] = know_df["rating"]
    know_df = know_df.join(wordlist_df.set_index("lemma"), "word")
    makedirs(figout, exist_ok=True)
    for participant, group_df in know_df.groupby("participant"):
        # TODO: modify freqknowfit to take column names
        fig, axs = plt.subplots(3, 3, sharex=True, sharey=True)
        fig.set_size_inches(12, 12)
        for ax, col in zip(axs.flatten(), COLS):
            group_df["zipf"] = np.log10(group_df[col] * 1000)
            draw_plot(group_df, ax, create_fit=False, ordinal=True, bw=bw)
        plt.tight_layout()
        fig.savefig(pjoin(figout, f"{participant}.png"))


if __name__ == "__main__":
    main()
