import seaborn
import pandas
import click
from wordfreq import cB_to_zipf, get_frequency_list
import matplotlib.pyplot as plt


@click.command()
@click.argument("inf", type=click.File("rb"))
@click.argument("figout")
def main(inf, figout):
    df = pandas.read_parquet(inf)
    wordfreq_zipfs = []
    for idx, bucket in enumerate(get_frequency_list("en")):
        for word in bucket:
            zipf = cB_to_zipf(-idx)
            wordfreq_zipfs.append(zipf)
    svl12k_zipf = df[df["respondent"] == 1]["zipf"]
    print(len(svl12k_zipf))
    print(len(wordfreq_zipfs))
    fig = plt.figure()
    seaborn.histplot(
        {
            "svl12k": svl12k_zipf,
            "all": wordfreq_zipfs,
        },
        stat="density",
        common_norm=False,
        kde=True
    )
    fig.savefig(figout)


if __name__ == "__main__":
    main()
