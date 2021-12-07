import click
import pandas

from sklearn.metrics import confusion_matrix, cohen_kappa_score, ConfusionMatrixDisplay
from matplotlib import pyplot as mpl


def clean_mark(col):
    return col.map(lambda x: int(x.strip().strip("b")))


@click.command()
@click.argument("annotation_a", type=click.File("r"))
@click.argument("annotation_b", type=click.File("r"))
@click.argument("figout", type=click.Path(), required=False)
def main(annotation_a, annotation_b, figout):
    df_a = pandas.read_csv(annotation_a, sep="\t")
    df_b = pandas.read_csv(annotation_b, sep="\t")
    df_joined = pandas.merge(
        df_a,
        df_b.drop(columns=["participant_id", "word", "lang", "type", "resp"]),
        on="response_id"
    )
    missing = df_joined[df_joined[["mark_x", "mark_y"]].isna().any(axis=1)]
    print(missing)
    df_clean = df_joined[["mark_x", "mark_y"]].dropna()
    df_clean["mark_x"] = clean_mark(df_clean["mark_x"])
    df_clean["mark_y"] = clean_mark(df_clean["mark_y"])
    print(
        "Cohen's Kappa",
        cohen_kappa_score(df_clean["mark_x"], df_clean["mark_y"])
    )
    print(
        "QWK",
        cohen_kappa_score(
            df_clean["mark_x"],
            df_clean["mark_y"],
            weights="quadratic"
        )
    )
    print("Confusion matrix")
    confmat = confusion_matrix(df_clean["mark_x"], df_clean["mark_y"])
    print(df_joined[df_joined["mark_x"] != df_joined["mark_y"]])
    ConfusionMatrixDisplay(confmat, display_labels=range(1, 6)).plot()
    mpl.ylabel("Annotator 1")
    mpl.xlabel("Annotator 2")
    mpl.savefig(figout)


if __name__ == "__main__":
    main()
