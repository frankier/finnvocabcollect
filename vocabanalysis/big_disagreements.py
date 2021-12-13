import click
import pandas

from sklearn.metrics import confusion_matrix, cohen_kappa_score


def clean_mark(col):
    return col.map(lambda x: int(x.strip().strip("b")))


@click.command()
@click.argument("annotation_a", type=click.File("r"))
@click.argument("annotation_b", type=click.File("r"))
@click.argument("disagreements", type=click.File("w"))
def main(annotation_a, annotation_b, disagreements):
    df_a = pandas.read_csv(annotation_a, sep="\t")
    df_b = pandas.read_csv(annotation_b, sep="\t")
    df_joined = pandas.merge(
        df_a,
        df_b.drop(columns=["participant_id", "word", "lang", "type", "resp"]),
        on="response_id"
    )
    df_clean = df_joined[["mark_x", "mark_y"]].copy()
    df_clean["mark_x"] = clean_mark(df_clean["mark_x"])
    df_clean["mark_y"] = clean_mark(df_clean["mark_y"])
    sorted_marks = df_clean.apply(
        lambda row: sorted([row["mark_x"], row["mark_y"]]),
        axis=1,
        result_type="expand"
    )
    sorted_marks.rename(columns={0: "mark_lo", 1: "mark_hi"}, inplace=True)
    df_joined = pandas.concat([df_joined, sorted_marks], axis=1)
    df_joined["mark_dist"] = df_joined["mark_hi"] - df_joined["mark_lo"]
    df_joined = df_joined[df_joined["mark_dist"] > 0]
    df_joined["mark_dist4"] = df_joined["mark_hi"].map(lambda x: min(x, 4)) - df_joined["mark_lo"].map(lambda x: min(x, 4))
    df_joined.sort_values(by=["mark_dist4", "mark_lo", "mark_dist"], ascending=[False, True, False], inplace=True)
    df_joined.to_csv(disagreements, sep="\t")


if __name__ == "__main__":
    main()
