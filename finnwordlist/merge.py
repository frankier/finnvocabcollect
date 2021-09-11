import random
import pandas
import numpy as np
import sys
from finnwordlist.multicorpusfreqs import iter_value_columns


def redistribute_compound_weights(df):
    compos_df = pandas.read_parquet("compound_compositionality.parquet")
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
    # We want to go long first so they redistribute their weights up the derivation tree
    rm_lemmas.sort(key=lambda lemma: len(lemma), reverse=True)
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


def drop_compositional_derivations(df):
    lemma_col_idx = df.columns.get_loc("lemma")
    deriv_df = pandas.read_parquet("suffixes.parquet")
    rm_lemmas = []
    # We want to go long first so they redistribute their weights up the derivation tree
    deriv_df.sort_values(
        by="derivs",
        ascending=False,
        inplace=True,
        key=lambda series: series.str.len()
    )
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


def drop_derivations_tradeoff(df):
    return redistribute_compound_weights(drop_compositional_derivations(df))
