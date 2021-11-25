import click
import pandas

from sklearn.metrics import confusion_matrix, cohen_kappa_score


def clean_mark(col):
    return col.map(lambda x: int(x.strip().strip("b")))


@click.command()
@click.argument("annotation_a", type=click.File("r"))
@click.argument("annotation_b", type=click.File("r"))
def main(annotation_a, annotation_b):
    df_a = pandas.read_csv(annotation_a, sep="\t")
    df_b = pandas.read_csv(annotation_b, sep="\t")
    df_joined = pandas.merge(
        df_a,
        df_b.drop(columns=["participant_id", "word", "lang", "type", "resp"]),
        on="response_id"
    )
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
    print(confusion_matrix(df_clean["mark_x"], df_clean["mark_y"]))
    print(df_joined[df_joined["mark_x"] != df_joined["mark_y"]])


if __name__ == "__main__":
    main()
