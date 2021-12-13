import click
import duckdb
from os import makedirs
from os.path import join as pjoin

from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
from matplotlib import pyplot as mpl
import numpy as np
from .queries import MARK_TRANSLATION_COMPARE_QUERY
from scipy.stats import kendalltau, somersd, spearmanr


def clean_mark(col):
    return col.map(lambda x: int(x.strip().strip("b")))


def plot_confmat(df, figout):
    rating_5 = (df["rating"] == 5).sum()
    reliability_5 = ((df["rating"] == 5) & (df["mark"] >= 4)).sum() / rating_5
    print("reliability_5", reliability_5)
    reliability_5_partial = ((df["rating"] == 5) & (df["mark"] >= 2)).sum() / rating_5
    print("reliability_5_partial", reliability_5_partial)
    rating_4 = (df["rating"] == 4).sum()
    print("reliability_4", ((df["rating"] == 4) & (df["mark"] >= 4)).sum() / rating_4)
    print("reliability_4_partial", ((df["rating"] == 4) & (df["mark"] >= 2)).sum() / rating_4)
    rating_lt3 = (df["rating"] <= 3).sum()
    underrating_lt3 = ((df["rating"] <= 3) & (df["mark"] >= 4)).sum() / rating_lt3
    print("underrating_lt3", underrating_lt3)
    underrating_lt3_partial = ((df["rating"] <= 3) & (df["mark"] >= 2)).sum() / rating_lt3
    print("underrating_lt3_partial", underrating_lt3_partial)
    print("balanced", ((1 - underrating_lt3) + reliability_5) / 2)
    print("balanced partial", ((1 - underrating_lt3_partial) + reliability_5_partial) / 2)
    print("kendalltau", kendalltau(df["rating"], df["mark"]).correlation)
    print("somersd", somersd(df["rating"], df["mark"]).statistic)
    print("spearmanr", spearmanr(df["rating"], df["mark"]).correlation)
    confmat = confusion_matrix(df["mark"], df["rating"])
    ConfusionMatrixDisplay(confmat, display_labels=range(1, 6)).plot()
    mpl.ylabel("Mark")
    mpl.xlabel("Rating")
    mpl.savefig(figout)


def not_extreme_disagreement(grp):
    sorted_grp = sorted(grp["mark"])
    return not (sorted_grp[0] <= 2 and sorted_grp[1] >= 4)


@click.command()
@click.argument("dbin", type=click.Path())
@click.argument("figout", type=click.Path())
@click.option("--filter", type=click.Choice(["none", "extreme-disagree", "any-disagree"]))
def main(dbin, figout, filter):
    conn = duckdb.connect(dbin)
    df = conn.execute(MARK_TRANSLATION_COMPARE_QUERY).fetchdf()
    df = df.dropna()
    df["mark"] = clean_mark(df["mark"])
    if filter == "any-disagree":
        df = df.groupby(["participant_id", "word"]).filter(
            lambda grp: len(np.unique(grp["mark"])) == 1
        )
        print(df)
        df = df.groupby(["participant_id", "word"]).min()
        print(df)
    elif filter == "extreme-disagree":
        df = df.groupby(["participant_id", "word"]).filter(not_extreme_disagreement)
        print(df)
        df = df.groupby(["participant_id", "word"]).min()
        print(df)
    makedirs(figout, exist_ok=True)
    print("* All *")
    plot_confmat(df, pjoin(figout, "all.png"))
    for pid, participant_df in df.groupby("participant_id"):
        print()
        print(f"* pid: {pid} *")
        plot_confmat(participant_df, pjoin(figout, f"p{pid}.png"))
    for lang, lang_df in df.groupby("language"):
        print()
        print(f"* lang: {lang} *")
        plot_confmat(lang_df, pjoin(figout, f"{lang}.png"))


if __name__ == "__main__":
    main()
