import random
import click
import pandas
from finnwordlist.utils.wordlists import read_bad_list, read_nss, DEFAULT_POS_FILTER
from pprint import pprint
import numpy as np
import sys


random.seed(0)


TARGET_LENGTH = 12000
CORPORA = [
    "s24",
    "klk",
    "lehdet",
    "wiki",
    "reddit",
    "opensub",
]

REL_FREQ_PREFIX = "relative_freq_"
ABS_FREQ_PREFIX = "abs_freq_"


# Filter out country names
# Filter out anything else which is not usually shown in its citation form?
# Filter out -kuu, -tai -- basically ordinal


def get_totals(freqs_df):
    totals = {}
    for corpus in CORPORA:
        totals[corpus] = freqs_df[ABS_FREQ_PREFIX + corpus].sum()
    return totals


def get_orders(freqs_df):
    orders = {}
    for corpus in CORPORA:
        orders[corpus] = iter((-freqs_df[ABS_FREQ_PREFIX + corpus]).argsort())
    return orders


def add_word_to_coverages(freqs_df, idx, coverages):
    for corpus in CORPORA:
        next_lemma_count = (
            freqs_df[ABS_FREQ_PREFIX + corpus].iloc[idx]
        )
        coverages[corpus] += next_lemma_count


def fill_to_limit(current_wordlist, coverages, totals, freqs_df, orders):
    while len(current_wordlist) < TARGET_LENGTH:
        coverages_sorted = (
            sorted(((v / totals[k], k) for k, v in coverages.items()))
        )
        lowest_coverage_corpus = coverages_sorted[0][1]
        while 1:
            idx = next(orders[lowest_coverage_corpus])
            next_lemma = freqs_df["lemma"].iloc[idx]
            if next_lemma not in current_wordlist:
                current_wordlist.append(next_lemma)
                add_word_to_coverages(freqs_df, idx, coverages)
                break


def take_from_all(current_wordlist, coverages, take_num, freqs_df, orders):
    new_words = []
    for corpus in CORPORA:
        taken = 0
        while taken < take_num:
            idx = next(orders[corpus])
            next_lemma = freqs_df["lemma"].iloc[idx]
            if next_lemma not in current_wordlist:
                new_words.append(next_lemma)
                current_wordlist.append(next_lemma)
                add_word_to_coverages(freqs_df, idx, coverages)
            taken += 1
    return new_words


def iter_value_columns():
    for corpus in CORPORA:
        for prefix in [REL_FREQ_PREFIX, ABS_FREQ_PREFIX]:
            yield prefix + corpus


def redistribute_compound_weights(df, current_wordlist):
    compos_df = pandas.read_parquet("compositionality.parquet")
    rm_lemmas = []
    highly_compositional_df = compos_df[compos_df["compositionality"] >= 0.9]
    rm_lemmas.extend(highly_compositional_df["compound"])
    num_non_compositional = (compos_df["compositionality"] < 0.7).sum()
    mid_range = compos_df[
        (compos_df["compositionality"] >= 0.7) &
        (compos_df["compositionality"] < 0.9)
    ]
    rm_lemmas.extend(mid_range["compound"])
    mid_range = mid_range.sample(frac=1)
    row_iter = mid_range.iterrows()
    num_mid_range_kept = 0
    for idx, row in row_iter:
        keep_prob = 1 - ((row["compositionality"] - 0.7) / 0.2)
        if random.random() < keep_prob:
            num_mid_range_kept += 1
            rm_lemmas.remove(row["compound"])
            if num_mid_range_kept >= num_non_compositional:
                break
    print("Removed", len(rm_lemmas))
    compound_col_idx = compos_df.columns.get_loc("compound")
    parts_col_idx = compos_df.columns.get_loc("parts")
    for lemma in rm_lemmas:
        compound_compos_idx = compos_df["compound"].searchsorted(lemma)
        if compos_df.iat[compound_compos_idx, compound_col_idx] != lemma:
            continue
        df_lemma_idx = df["lemma"].searchsorted(lemma)
        if (
            df_lemma_idx >= len(df) or
            df.iat[df_lemma_idx, df.columns.get_loc("lemma")] != lemma
        ):
            print("Couldn't find compound", lemma, file=sys.stderr)
            continue
        parts = compos_df.iat[compound_compos_idx, parts_col_idx]
        found_parts = []
        for part in parts:
            df_part_idx = df["lemma"].searchsorted(part)
            if df.iat[df_part_idx, df.columns.get_loc("lemma")] != part:
                print("Couldn't find part", lemma, file=sys.stderr)
                continue
            found_parts.append((df_part_idx, part))
        for df_part_idx, part in found_parts:
            for value_col in iter_value_columns():
                col_loc = df.columns.get_loc(value_col)
                df.iat[df_part_idx, col_loc] += \
                    df.iat[df_lemma_idx, col_loc] / len(found_parts)
    return df[~df["lemma"].isin(rm_lemmas)]


def drop_compositional_derivations(df, current_wordlist):
    lemma_col_idx = df.columns.get_loc("lemma")
    deriv_df = pandas.read_parquet("deriv.parquet")
    rm_lemmas = []
    for _, row in deriv_df.iterrows():
        deriv = row["derivs"]
        deriv_idx = df["lemma"].searchsorted(deriv)
        if df.iat[deriv_idx, lemma_col_idx] != deriv:
            print("Couldn't find derived term", deriv, file=sys.stderr)
            continue
        heads = row["heads"]
        found_heads = []
        for head in heads:
            head_idx = df["lemma"].searchsorted(head)
            if df.iat[head_idx, lemma_col_idx] != head:
                print("Couldn't find head of derived term", head, file=sys.stderr)
                continue
            found_heads.append((head_idx, head))
        for head_idx, head in found_heads:
            for value_col in iter_value_columns():
                col_loc = df.columns.get_loc(value_col)
                df.iat[head_idx, col_loc] += df.iat[deriv_idx, col_loc] / len(found_heads)
        rm_lemmas.append(row["derivs"])
    print("Removed", len(rm_lemmas))
    return df[~df["lemma"].isin(rm_lemmas)]


def merge_duplicates(df):
    df.sort_values("lemma", inplace=True)
    last = None
    last_idx = None
    keep = np.full(len(df), True)
    for idx, (_, row) in enumerate(df.iterrows()):
        lemma = row["lemma"]
        if lemma == last:
            keep[idx] = False
            for value_col in iter_value_columns():
                df.iat[last_idx, df.columns.get_loc(value_col)] += row[value_col]
        last = lemma
        last_idx = idx
    return df[keep]


def recalculate_coverages(freqs_df, current_wordlist):
    coverages = {}
    for corpus in CORPORA:
        coverages[corpus] = freqs_df[ABS_FREQ_PREFIX + corpus][freqs_df["lemma"].isin(current_wordlist)].sum()
    return coverages


@click.command()
@click.argument("vectors")
@click.argument("inf")
@click.argument("outf")
def main(vectors, inf, outf):
    nss = read_nss(False)
    freqs_df = pandas.read_parquet(inf)
    # Filter according to NSS
    freqs_df = freqs_df[freqs_df["lemma"].isin(nss)]
    # Filter according to POS
    freqs_df = freqs_df[freqs_df["pos"].isin(DEFAULT_POS_FILTER)]
    # Merge duplicates
    freqs_df = merge_duplicates(freqs_df)
    # Filter according to not being
    # a country/language (proper noun-ish)
    # or day specifier (ordinal-ish)
    bad_list = read_bad_list()
    freqs_df = freqs_df[~freqs_df["lemma"].isin(bad_list)]

    # Set up for taking wordlist from freqs
    totals = get_totals(freqs_df)
    orders = get_orders(freqs_df)
    current_wordlist = []
    coverages = {col: 0 for col in CORPORA}

    def print_coverages():
        for k, v in coverages.items():
            print(k, v / totals[k] * 100)

    # Take so we have 2000 from each regardless of anything else
    first_words = take_from_all(current_wordlist, coverages, 2000, freqs_df, orders)
    print("Taken 2000 from each")
    print(len(current_wordlist))
    print("Coverages")
    print_coverages()
    print()

    # Remove very compositional derivations and compounds
    print("Totals")
    pprint(totals)
    print("Dropping compositional derivations")
    freqs_df = drop_compositional_derivations(freqs_df, current_wordlist)
    print("Have", len(freqs_df), "left")
    print_coverages()
    print()

    print("Totals after trimming derivations")
    pprint(totals)
    pprint(get_totals(freqs_df))

    print("Trimming compounds")
    freqs_df = redistribute_compound_weights(freqs_df, current_wordlist)

    print("Totals after trimming compounds")
    pprint(totals)
    pprint(get_totals(freqs_df))

    coverages = recalculate_coverages(freqs_df, current_wordlist)

    print("Coverages after trimming derivations and compounds")
    print_coverages()
    print()

    # Must recompute these after trimming
    totals = get_totals(freqs_df)
    orders = get_orders(freqs_df)

    # Fill up to 90% coverage of all corpora
    fill_to_limit(current_wordlist, coverages, totals, freqs_df, orders)

    print("Taken up to 90% coverage")
    print(len(current_wordlist))
    print("Coverages")
    print_coverages()

    freqs_df = freqs_df[freqs_df["lemma"].isin(current_wordlist)]
    freqs_df.drop(columns=["pos"], inplace=True)

    freqs_df.to_parquet(outf)
    print(len(current_wordlist))


if __name__ == "__main__":
    main()
