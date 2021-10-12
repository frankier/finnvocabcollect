import click
import pandas
from finnwordlist.utils.wordlists import read_word_list


@click.command()
@click.argument("df_in", type=click.File("rb"))
@click.argument("words_in")
@click.argument("df_out", type=click.File("wb"))
def main(df_in, words_in, df_out):
    df = pandas.read_parquet(df_in)
    df = df[df["lemma"].isin(read_word_list(words_in))]
    df.to_parquet(df_out)


if __name__ == "__main__":
    main()
