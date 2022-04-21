import click
import duckdb
from seaborn import pairplot
import matplotlib.pyplot as plt
from os import makedirs
from os.path import join as pjoin


QUERY = """
select
    participant.cefr_selfassess_reading_comprehension,
    participant.lived_in_finland,
    reliabilities.reliability_5,
    reliabilities.underrating_lt3_partial,
    reliabilities.balanced,
    reliabilities.kendalltau,
    (select sum(selfassess_session.time_secs)
     from selfassess_session
     where selfassess_session.participant_id = participant.id) as time,
    participant_language.language
from participant
join reliabilities
    on reliabilities.participant_id = participant.id
join participant_language
    on participant_language.participant_id = participant.id
where
    participant_language.level = 7;
"""


@click.command()
@click.argument("dbin", type=click.Path())
@click.argument("figout", type=click.Path())
def main(dbin, figout):
    conn = duckdb.connect(dbin)
    df = conn.execute(QUERY).fetchdf()
    print(df)
    df["language"] = df["language"].map(lambda x: ["en", "ru", "hu"].index(x))
    makedirs(figout, exist_ok=True)
    df["time"] = df["time"] / 3600

    pairplot(df)
    plt.tight_layout()
    plt.savefig(pjoin(figout, "pairplot.png"))

    plt.subplots()
    plt.scatter(df["cefr_selfassess_reading_comprehension"], df["time"])
    plt.xlabel("CEFR reading level")
    plt.ylabel("Self-assessment completion time (hours)")
    plt.ylim(bottom=0)
    plt.xticks([3, 4, 5, 6], ["B1", "B2", "C1", "C2"])
    plt.tight_layout()
    plt.savefig(pjoin(figout, "cefr_v_time.png"))

    plt.subplots()
    plt.scatter(df["time"], df["balanced"])
    plt.xlabel("Self-assessment completion time (hours)")
    plt.ylabel("Balanced reliability")
    plt.xlim(left=0)
    plt.ylim(top=1)
    plt.tight_layout()
    plt.savefig(pjoin(figout, "time_v_balanced.png"))

    plt.subplots()
    plt.scatter(df["cefr_selfassess_reading_comprehension"], df["balanced"])
    plt.xticks([3, 4, 5, 6], ["B1", "B2", "C1", "C2"])
    plt.xlabel("CEFR reading level")
    plt.ylabel("Balanced reliability")
    plt.ylim(top=1)
    plt.tight_layout()
    plt.savefig(pjoin(figout, "cefr_v_balanced.png"))

    plt.subplots()
    plt.scatter(df["lived_in_finland"], df["balanced"])
    plt.tight_layout()
    plt.savefig(pjoin(figout, "lived_v_balanced.png"))

    plt.subplots()
    plt.scatter(df["lived_in_finland"], df["time"])
    plt.tight_layout()
    plt.savefig(pjoin(figout, "lived_v_time.png"))


if __name__ == "__main__":
    main()
