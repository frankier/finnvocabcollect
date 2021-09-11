import seaborn
import pandas
import click
import matplotlib.pyplot as plt
import numpy as np


@click.command()
@click.argument("allin", type=click.File("rb"))
@click.argument("wordlistin", type=click.File("rb"))
@click.argument("figout")
def main(allin, wordlistin, figout):
    # TODO: Figure skating
    all_df = pandas.read_parquet(allin)
    zipf_all = np.log10(all_df["average_relative"] * 1000)
    wordlist_df = pandas.read_parquet(wordlistin)
    zipf_wordlist = np.log10(wordlist_df["average_relative"] * 1000)
    fig = plt.figure()
    seaborn.histplot(
        {
            "wordlist": zipf_wordlist,
            "all": zipf_all,
        },
        stat="density",
        common_norm=False,
        kde=True
    )
    fig.savefig(figout)


if __name__ == "__main__":
    main()
