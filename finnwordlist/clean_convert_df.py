import click
import pandas


@click.command()
@click.argument("in_csv")
@click.argument("out_parquet")
def main(in_csv, out_parquet):
    freqs_df = pandas.read_csv(in_csv)
    freqs_df.rename(
        columns={"POS_CLASS": "pos"},
        inplace=True
    )
    freqs_df.rename(
        columns=lambda name: name.lower(),
        inplace=True
    )
    freqs_df.to_parquet(out_parquet)


if __name__ == "__main__":
    main()
