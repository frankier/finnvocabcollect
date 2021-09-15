import click
import pandas
from finnwordlist.merge import drop_derivations_tradeoff


@click.command()
@click.argument("inf")
@click.argument("outf")
def main(inf, outf):
    # Remove very compositional derivations and compounds
    print("Dropping compositional derivations and trimming compounds")
    drop_derivations_tradeoff(pandas.read_parquet(inf)).to_parquet(outf)


if __name__ == "__main__":
    main()
