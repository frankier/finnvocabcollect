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


def iter_value_columns():
    for corpus in CORPORA:
        for prefix in [REL_FREQ_PREFIX, ABS_FREQ_PREFIX]:
            yield prefix + corpus


def recalculate_coverages(freqs_df, current_wordlist):
    coverages = {}
    for corpus in CORPORA:
        coverages[corpus] = freqs_df[ABS_FREQ_PREFIX + corpus][freqs_df["lemma"].isin(current_wordlist)].sum()
    return coverages
