import click
import duckdb
import pandas
from os import makedirs
from os.path import join as pjoin

from sklearn.metrics import confusion_matrix, cohen_kappa_score, ConfusionMatrixDisplay
from matplotlib import pyplot as mpl

from .queries import MARKER_COMPARE_QUERY


def clean_mark(col):
    return col.map(lambda x: int(x.strip().strip("b")))


def dump_disagreements(df, figout):
    print(
        "Cohen's Kappa",
        cohen_kappa_score(df["mark1"], df["mark2"])
    )
    print(
        "QWK",
        cohen_kappa_score(
            df["mark1"],
            df["mark2"],
            weights="quadratic"
        )
    )
    print("Confusion matrix")
    confmat = confusion_matrix(df["mark1"], df["mark2"])
    print(df[df["mark1"] != df["mark2"]])
    ConfusionMatrixDisplay(confmat, display_labels=range(1, 6)).plot()
    mpl.ylabel("Annotator 1")
    mpl.xlabel("Annotator 2")
    mpl.savefig(figout)


@click.command()
@click.argument("dbin", type=click.Path())
@click.argument("figout", type=click.Path())
def main(dbin, figout):
    conn = duckdb.connect(dbin)
    df = conn.execute(MARKER_COMPARE_QUERY).fetchdf()
    print(df)
    df["mark1"] = clean_mark(df["mark1"])
    df["mark2"] = clean_mark(df["mark2"])
    makedirs(figout, exist_ok=True)
    dump_disagreements(df, pjoin(figout, "all.png"))
    for pid, participant_df in df.groupby("participant_id"):
        print()
        print(f"Participant {pid}")
        dump_disagreements(participant_df, pjoin(figout, f"p{pid}.png"))
    for lang, lang_df in df.groupby("language"):
        print()
        print(f"Language {lang}")
        dump_disagreements(lang_df, pjoin(figout, f"{lang}.png"))


if __name__ == "__main__":
    main()
