import click
import pandas
from finnwordlist.utils.wordlists import read_nss, DEFAULT_POS_FILTER
from finnwordlist.merge import merge_duplicates
from finnwordlist.aggs import add_aggs


@click.command()
@click.argument("inf")
@click.argument("outf")
def main(inf, outf):
    nss = read_nss(False)
    freqs_df = pandas.read_parquet(inf)
    # Filter according to NSS
    freqs_df = freqs_df[freqs_df["lemma"].isin(nss)]
    # Filter according to POS
    freqs_df = freqs_df[freqs_df["pos"].isin(DEFAULT_POS_FILTER)]
    # Merge duplicates
    freqs_df = merge_duplicates(freqs_df)
    freqs_df.drop(columns="pos", inplace=True)
    # Add agg columns
    add_aggs(freqs_df)
    # Save
    freqs_df.to_parquet(outf)


if __name__ == "__main__":
    main()
