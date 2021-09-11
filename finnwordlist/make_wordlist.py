import random
import click
import pandas
from finnwordlist.utils.wordlists import read_bad_list, read_nss, DEFAULT_POS_FILTER
from finnwordlist.merge import redistribute_compound_weights, drop_compositional_derivations, merge_duplicates, drop_derivations_tradeoff
from pprint import pprint
import numpy as np
import sys
from finnwordlist.multicorpusfreqs import CORPORA, get_totals, get_orders, add_word_to_coverages, recalculate_coverages


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
    print("Dropping compositional derivations and trimming compounds")
    part_derivs_df = drop_derivations_tradeoff(freqs_df.copy())

    #coverages = recalculate_coverages(freqs_df, current_wordlist)

    print("Coverages after trimming derivations and compounds")
    print_coverages()
    print()

    # Must recompute these after trimming
    totals = get_totals(part_derivs_df)
    orders = get_orders(part_derivs_df)

    part_derivs_coverages = recalculate_coverages(part_derivs_df, current_wordlist)

    # Fill up to 90% coverage of all corpora
    fill_to_limit(current_wordlist, part_derivs_coverages, totals, freqs_df, orders)

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
