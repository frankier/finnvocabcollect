import sys
import click
import pandas
from finnwordlist.utils.wordlists import read_word_list
from pathlib import Path


@click.command()
@click.argument("target", type=int)
@click.argument(
    "current_wordlist",
    type=click.Path(path_type=Path, exists=True)
)
@click.argument("source_wordlist", type=click.File("rb"))
def main(target, current_wordlist, source_wordlist):
    source_df = pandas.read_parquet(source_wordlist)
    source_df.sort_values(
        by="agg_rel_freq_figure_skating",
        inplace=True,
        ascending=False
    )
    existing_words = read_word_list(current_wordlist)
    got = 0
    for lemma in source_df["lemma"]:
        if lemma in existing_words:
            continue
        print(lemma)
        got += 1
        if got >= target:
            break
    if got < target:
        print(f"Could not reach target, only got {got}", file=sys.stderr)


if __name__ == "__main__":
    main()
