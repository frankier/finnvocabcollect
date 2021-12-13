import click
import duckdb
from scipy.stats import kendalltau


RELIABILITIES_TABLE = """
create table reliabilities (
    participant_id int,
    reliability_5 float,
    reliability_5_partial float,
    reliability_4 float,
    reliability_4_partial float,
    underrating_lt3 float,
    underrating_lt3_partial float,
    balanced float,
    balanced_partial float,
    kendalltau float
);
"""


MARK_TRANSLATION_COMPARE_QUERY = """
select
    selfassess_session.participant_id,
    participant_language.language,
    miniexam_response.word,
    selfassess_response.rating,
    miniexam_mark.marker,
    miniexam_mark.mark
from selfassess_session
join selfassess_response
    on selfassess_session.id = selfassess_response.session_id
join miniexam_response
    on selfassess_session.participant_id = miniexam_response.participant_id
    and miniexam_response.word = selfassess_response.word
join miniexam_mark
    on miniexam_mark.selfassess_response_id = miniexam_response.id
join participant_language
    on selfassess_session.participant_id = participant_language.participant_id
where
    participant_language.level = 7;
"""


def clean_mark(col):
    return col.map(lambda x: int(x.strip().strip("b")))


def not_extreme_disagreement(grp):
    sorted_grp = sorted(grp["mark"])
    return not (sorted_grp[0] <= 2 and sorted_grp[1] >= 4)


@click.command()
@click.argument("db", type=click.Path())
def main(db):
    conn = duckdb.connect(db)
    conn.execute("drop table reliabilities;")
    conn.execute(RELIABILITIES_TABLE)
    df_all = conn.execute(MARK_TRANSLATION_COMPARE_QUERY).fetchdf()
    df_all["mark"] = clean_mark(df_all["mark"])
    df_all = df_all.groupby(["participant_id", "word"]).filter(not_extreme_disagreement)
    df_all = df_all.groupby(["participant_id", "word"]).min()
    for pid, df in df_all.groupby("participant_id"):
        rating_5 = (df["rating"] == 5).sum()
        reliability_5 = ((df["rating"] == 5) & (df["mark"] >= 4)).sum() / rating_5
        reliability_5_partial = ((df["rating"] == 5) & (df["mark"] >= 2)).sum() / rating_5
        rating_4 = (df["rating"] == 4).sum()
        rating_lt3 = (df["rating"] <= 3).sum()
        reliability_4 = ((df["rating"] == 4) & (df["mark"] >= 4)).sum() / rating_4
        reliability_4_partial = ((df["rating"] == 4) & (df["mark"] >= 2)).sum() / rating_4
        underrating_lt3 = ((df["rating"] <= 3) & (df["mark"] >= 4)).sum() / rating_lt3
        underrating_lt3_partial = ((df["rating"] <= 3) & (df["mark"] >= 2)).sum() / rating_lt3
        balanced = ((1 - underrating_lt3) + reliability_5) / 2
        balanced_partial = ((1 - underrating_lt3_partial) + reliability_5_partial) / 2
        kt = kendalltau(df["rating"], df["mark"]).correlation
        conn.execute(
            "insert into reliabilities values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                pid,
                reliability_5,
                reliability_5_partial,
                reliability_4,
                reliability_4_partial,
                underrating_lt3,
                underrating_lt3_partial,
                balanced,
                balanced_partial,
                kt
            )
        )


if __name__ == "__main__":
    main()
