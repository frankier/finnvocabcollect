import seaborn
import pandas
import click
import matplotlib.pyplot as plt
import numpy as np
from finnwordlist.multicorpusfreqs import REL_FREQ_COLS
from finnwordlist.aggs import AGG_COLS

COLS = [
    *AGG_COLS,
    *REL_FREQ_COLS
]


@click.command()
@click.argument("allin", type=click.File("rb"))
@click.argument("wordlistin", type=click.File("rb"))
@click.argument("figout")
def main(allin, wordlistin, figout):
    all_df = pandas.read_parquet(allin)
    wordlist_df = pandas.read_parquet(wordlistin)
    #wordlist_df = wordlist_df[wordlist_df["is_core"]]
    fig, axs = plt.subplots(3, 3, sharex=True, sharey=True)
    fig.set_size_inches(12, 12)
    for ax, col in zip(axs.flatten(), COLS):
        ax.set_title(col)
        zipf_all = np.log10(all_df[col] * 1000)
        zipf_wordlist = np.log10(wordlist_df[col] * 1000)
        seaborn.histplot(
            {
                "wordlist": zipf_wordlist,
                "all": zipf_all,
            },
            stat="density",
            common_norm=False,
            kde=True,
            ax=ax
        )
    axs[0, 0].set_ylim(top=0.8)
    plt.tight_layout()
    fig.savefig(figout)


if __name__ == "__main__":
    main()
