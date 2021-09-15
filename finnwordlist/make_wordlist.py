from math import log10, isnan
import random
import click
import pandas
from finnwordlist.aggs import add_aggs
from finnwordlist.utils.wordlists import read_bad_list, read_nss, DEFAULT_POS_FILTER
from finnwordlist.merge import redistribute_compound_weights, drop_compositional_derivations, merge_duplicates, drop_derivations_tradeoff
from pprint import pprint
import numpy as np
import sys
import scipy.stats as stats
from finnwordlist.multicorpusfreqs import CORPORA, REL_FREQ_PREFIX, REL_FREQ_COLS, get_totals, get_orders, add_word_to_coverages, recalculate_coverages
from finnwordlist.utils.stats import kde_mode


random.seed(0)


TARGET_LENGTH = 12000
# Filter out country names
# Filter out anything else which is not usually shown in its citation form?
# Filter out -kuu, -tai -- basically ordinal


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


def zipf_to_rel(zipf):
    return 10 ** -3 * (10 ** zipf)


def rel_to_bucket(rel, min_zipf=2, max_bucket=float("inf")):
    if rel == 0:
        return None
    bucket_idx = int((log10(rel * 10 ** 3) - min_zipf) * 10)
    if bucket_idx < 0 or bucket_idx >= max_bucket:
        return None
    return bucket_idx


def mode_freq(freqs):
    kernel = stats.gaussian_kde(freqs)
    mode = kde_mode(kernel, freqs)
    print("mode", mode)
    return mode


def fill_freq_range(freqs_df, current_wordlist):
    freqs_df["max_tmp"] = freqs_df[REL_FREQ_COLS].max(axis=1)
    freq_cols = [*REL_FREQ_COLS, "max_tmp"]
    in_wordlist = freqs_df["lemma"].isin(current_wordlist)
    current_freqs = freqs_df[in_wordlist]
    max_buckets = [rel_to_bucket(mode_freq(current_freqs[col].to_numpy())) for col in freq_cols]
    print("max_buckets", max_buckets)
    max_bucket = max(max_buckets)
    buckets = np.zeros((len(freq_cols), max_bucket))
    for idx, mb in enumerate(max_buckets):
        buckets[idx, mb:] = float("inf")
    ends = zipf_to_rel(np.linspace(2, 2 + 0.1 * max_bucket, max_bucket + 1))
    print("ends", ends)
    for _, word_row in current_freqs.iterrows():
        #print("word_row", word_row)
        freqs = [word_row[col] for col in freq_cols]
        for idx, freq in enumerate(freqs):
            #print(word_row["lemma"], idx, bucket_idx_float)
            bucket_idx = rel_to_bucket(freq, max_bucket=max_bucket)
            if bucket_idx is None:
                continue
            buckets[idx, bucket_idx] += 1
    print("Buckets!")
    print(buckets)
    cand_freqs = freqs_df[~in_wordlist].sample(frac=1)
    while len(current_wordlist) < TARGET_LENGTH:
        index = np.unravel_index([np.argmin(buckets)], buckets.shape)
        freq_col_idx = index[0][0]
        bucket_idx = index[1][0]
        #print("freq_col_idx, bucket_idx", freq_col_idx, bucket_idx)
        freq_col = freq_cols[freq_col_idx]
        cur_cands = (
            (cand_freqs[freq_col] >= ends[bucket_idx]) &
            (cand_freqs[freq_col] < ends[bucket_idx + 1])
        )
        if not any(cur_cands):
            print("Impossible bucket", freq_col_idx, bucket_idx)
            if buckets[freq_col_idx, bucket_idx] == float("inf"):
                print("All buckets impossible. Cannot continue")
                sys.exit(-1)
            buckets[freq_col_idx, bucket_idx] = float("inf")
            continue
        cur_cand_idx = cand_freqs.index[cur_cands][0]
        # Add to all
        for other_freq_col_idx, (other_freq_col, other_max_bucket) in enumerate(zip(freq_cols, max_buckets)):
            other_rel = cand_freqs.at[cur_cand_idx, other_freq_col]
            other_bucket_idx = rel_to_bucket(other_rel, max_bucket=other_max_bucket)
            if other_bucket_idx is None:
                continue
            buckets[other_freq_col_idx, other_bucket_idx] += 1
        current_wordlist.append(cand_freqs.at[cur_cand_idx, "lemma"])
        cand_freqs.drop(index=cur_cand_idx, inplace=True)
    print("Buckets end!")
    print(buckets)
    freqs_df.drop(columns="max_tmp", inplace=True)


@click.command()
@click.argument("inf")
@click.argument("derivtrim_inf")
@click.argument("outf")
def main(inf, derivtrim_inf, outf):
    freqs_df = pandas.read_parquet(inf)
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

    derivtrim_df = pandas.read_parquet(derivtrim_inf)

    #coverages = recalculate_coverages(freqs_df, current_wordlist)

    print("Coverages after trimming derivations and compounds")
    print_coverages()
    print()

    # Must recompute these after trimming
    totals = get_totals(derivtrim_df)
    orders = get_orders(derivtrim_df)
    derivs_coverages = recalculate_coverages(derivtrim_df, current_wordlist)

    first_words_derivs = take_from_all(current_wordlist, derivs_coverages, 2000, derivtrim_df, orders)

    # Fill up to 90% coverage of all corpora
    #fill_to_limit(current_wordlist, part_derivs_coverages, totals, derivtrim_df, orders)
    print("derivtrim_df", derivtrim_df)
    print("freqs_df", freqs_df)
    #import sys; sys.exit()
    fill_freq_range(derivtrim_df, current_wordlist)

    print("Filled up!")
    print(len(current_wordlist))
    print("Coverages")
    print_coverages()

    freqs_df = freqs_df[freqs_df["lemma"].isin(current_wordlist)]
    freqs_df["is_core"] = freqs_df["lemma"].isin(first_words)
    freqs_df["is_derivtrim_core"] = freqs_df["lemma"].isin(derivtrim_df)

    # Refresh agg columns
    add_aggs(freqs_df)

    freqs_df.to_parquet(outf)
    print(len(current_wordlist))


if __name__ == "__main__":
    main()
