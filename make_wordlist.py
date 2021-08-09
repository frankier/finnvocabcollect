import sys
import numpy
import click
from lxml import etree
import pandas
from functools import reduce
import numpy as np
import os
from os.path import join as pjoin


NSS_XML_PATH = "kotus-sanalista_v1/kotus-sanalista_v1.xml"
COMPOUND_LIST = "compound_list.txt"


DEFAULT_POS_FILTER = ["V", "N", "A", "Adv", "Adp"]
ALL_POS = [*DEFAULT_POS_FILTER, "Pron", "Num", "C", "Interj"]
PRODUCTIVE_DERIVATIONS = [
    # -ly
    ("Adv", "sti"),
    # -less
    ("A", "ton"),
    ("A", "tön"),
    # -ness
    ("N", "yys"),
    ("N", "uus"),
]


def read_compound_list():
    res = set()
    with open(COMPOUND_LIST) as compounds:
        for line in compounds:
            word = line.strip()
            if word:
                res.add(word.lower())
    return res


def read_nss(no_compound=False):
    res = set()
    if no_compound:
        compound_list = read_compound_list()
    for elem in etree.parse(NSS_XML_PATH).xpath("//s"):
        if no_compound:
            if "-" in elem.text or " " in elem.text:
                continue
            if elem.text in compound_list:
                continue
            tns = elem.xpath("..//tn")
            if not tns:
                continue
            if tns[0].text in ("50", "51"):
                continue
        res.add(elem.text)
    return res


@click.command()
@click.option("--output-fmt", type=click.Choice(["csv", "txt"]))
@click.option(
    "--pos",
    type=click.Choice(ALL_POS),
    multiple=True,
    default=DEFAULT_POS_FILTER
)
@click.option("--shuffle/--no-shuffle")
@click.option(
    "--filter",
    type=click.Choice([
        "none-no-pos",
        "none",
        "nss-present",
        "nss-no-compound"
    ]),
    default="none"
)
@click.option("--drop-dupes/--keep-dupes")
@click.option("--drop-reg-der/--keep-reg-der")
@click.option("--size", type=int, required=False)
@click.option("--intermediates-out", type=click.Path())
def main(
    output_fmt,
    pos,
    shuffle,
    filter,
    drop_dupes,
    drop_reg_der,
    size,
    intermediates_out,
):
    if intermediates_out:
        os.makedirs(intermediates_out, exist_ok=True)

    freqs_df = pandas.read_parquet("freqs.parquet")
    freqs_df["zipf"] = np.log10(1e9 * freqs_df["freq"])

    def keep_rows(keep_condition, out_base):
        nonlocal freqs_df
        if intermediates_out:
            out_path = pjoin(intermediates_out, out_base)
            filtered_df = freqs_df[~keep_condition]
            print(f"Saving {len(filtered_df)} rows to {out_base}", file=sys.stderr)
            filtered_df.to_csv(out_path, index=False)
        freqs_df = freqs_df[keep_condition]

    if drop_dupes:
        # We drop dupes early so that we don't end up with e.g. minä
        freqs_df.drop_duplicates("lemma", inplace=True)

    if filter not in ("none-no-pos", "none"):
        nss = read_nss(False)
        keep_rows(freqs_df["lemma"].isin(nss), "out_of_nss.csv")
        if filter == "nss-no-compound":
            nss = read_nss(True)
            keep_rows(freqs_df["lemma"].isin(nss), "compounds.csv")
        del nss

    if filter != "none-no-pos":
        keep_rows(freqs_df["pos"].isin(pos), "nopos.csv")

    if drop_reg_der:
        keep_rows(
            ~reduce(lambda a, b: a | b, (
                freqs_df["lemma"].str.endswith(prod_suffix)
                & (freqs_df["pos"] == prod_pos)
                for prod_pos, prod_suffix
                in PRODUCTIVE_DERIVATIONS
            )),
            "drop_reg_der.csv"
        )

    if size is not None:
        freqs_df = freqs_df.head(size)

    if shuffle:
        freqs_df = freqs_df.sample(frac=1).reset_index(drop=True)

    print(f"Saving {len(freqs_df)} rows to stdout")
    for zipf in numpy.linspace(7, 0, num=15):
        print(len(freqs_df[freqs_df['zipf'] > zipf]), "rows with zipf >", zipf, file=sys.stderr)

    freqs_df.to_csv(sys.stdout, index=False)


if __name__ == "__main__":
    main()
