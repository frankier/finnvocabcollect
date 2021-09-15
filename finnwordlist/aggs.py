from statistics import mean
from finnwordlist.multicorpusfreqs import REL_FREQ_COLS


AGG_COLS = [
    "agg_rel_freq_figure_skating",
    "agg_rel_freq_min",
    "agg_rel_freq_max",
]


def figure_skating_metric_row(row):
    return mean(sorted(row[REL_FREQ_COLS])[1:-1])


def add_aggs(freqs_df):
    freqs_df["agg_rel_freq_figure_skating"] = freqs_df.apply(
        figure_skating_metric_row,
        axis="columns"
    )
    freqs_df["agg_rel_freq_min"] = freqs_df[REL_FREQ_COLS].min(axis=1)
    freqs_df["agg_rel_freq_max"] = freqs_df[REL_FREQ_COLS].max(axis=1)
