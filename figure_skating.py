import click
import pandas
from statistics import mean


LEMMAS_CSV_PATH = "lemma_freqs.csv"
FREQ_COLS = [
    "RELATIVE_FREQ_S24",
    "RELATIVE_FREQ_KLK",
    "RELATIVE_FREQ_LEHDET",
    "RELATIVE_FREQ_WIKI",
    "RELATIVE_FREQ_REDDIT",
    "RELATIVE_FREQ_OPENSUB",
]


def figure_skating_metric_row(row):
    return mean(sorted(row[FREQ_COLS])[1:-1])


@click.command()
def main():
    freqs_df = pandas.read_csv(LEMMAS_CSV_PATH)
    freqs_df["freq"] = freqs_df.apply(
        figure_skating_metric_row,
        axis="columns"
    )
    freqs_df["freq"] /= freqs_df["freq"].sum()
    freqs_df.drop(
        freqs_df.columns.difference(["LEMMA", "POS_CLASS", "freq"]),
        1,
        inplace=True,
    )
    freqs_df.rename(
        columns={"LEMMA": "lemma", "POS_CLASS": "pos"},
        inplace=True
    )
    freqs_df.sort_values(by=["freq"], inplace=True, ascending=False)
    freqs_df.reset_index(drop=True, inplace=True)
    freqs_df.to_parquet("freqs.parquet")


if __name__ == "__main__":
    main()
