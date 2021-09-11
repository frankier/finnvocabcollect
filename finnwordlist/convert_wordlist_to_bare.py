import click
import pandas


@click.command()
@click.argument("inf")
@click.argument("outf", type=click.File("w"))
def main(inf, outf):
    df = pandas.read_parquet(inf)

    for lemma in df["lemma"]:
        print(lemma, file=outf)
