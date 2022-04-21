import click
import duckdb
import numpy
import pandas
from selfassess.utils import get_session
from selfassess.quali import CEFR_SKILLS
from .utils import get_participant_sessions
from selfassess.queries import participant_timeline_query
from datetime import timedelta


CEFR_FIELDS = [
    f"cefr_{type}_{skill}"
    for type in ("selfassess", "proof")
    for skill in CEFR_SKILLS
]


PARTICIPANT_TABLE = """
create table participant (
    id int primary key,
    {}
    lived_in_finland int,
    proof_age varchar,
    proof_type varchar,
    miniexam_time_secs int,
    miniexam_day int
);
""".format(
    "\n".join((f"{field} int," for field in CEFR_FIELDS))
)


def setup_duckdb(db_out):
    conn = duckdb.connect(db_out)

    print("Creating tables")
    conn.execute(
        PARTICIPANT_TABLE +
        """
    create table participant_language (
        participant_id int,
        language varchar,
        level int
    );
    create table selfassess_session (
        id int primary key,
        participant_id int,
        device varchar,
        time_secs int,
        day int
    );
    create table selfassess_response (
        session_id int,
        word varchar,
        time_usecs int64,
        rating int
    );
    create table miniexam_response (
        id int primary key,
        participant_id int,
        word varchar,
        type varchar,
        lang varchar,
        response varchar,
        grade int
    );
    create table miniexam_mark (
        selfassess_response_id int,
        marker varchar,
        mark varchar
    );
    """)
    return conn


# .mode csv\n.sep '\t'\nCREATE TABLE $3 AS SELECT * FROM read_csv_auto('head.tsv', HEADER=TRUE)


def flush_rows(schema, conn, rows):
    if not rows:
        return
    df = pandas.DataFrame(rows)
    conn.register('df', df)
    conn.execute(f"INSERT INTO {schema} SELECT * FROM df;")
    conn.unregister('df')
    rows.clear()
    conn.commit()


@click.command()
@click.argument("db_out", type=click.Path())
@click.option(
    "--which",
    type=click.Choice(["all", "complete", "incomplete"]),
    default="all"
)
@click.option(
    "--marking",
    multiple=True,
)
@click.option(
    "--use-original-ids/--renumber-ids",
)
def main(db_out, which, marking, use_original_ids):
    # Inefficient ORM usage here
    # -- but there are 15 items and this runs as a batch job
    ddb_conn = setup_duckdb(db_out)
    sqlite_sess = get_session()
    participants = sqlite_sess.execute(participant_timeline_query()).scalars()
    mark_lookups = {}
    for annotator_num, mark_info in enumerate(marking, start=1):
        label, path = mark_info.split(":", 1)
        with open(path, "r") as mark_file:
            df = pandas.read_csv(mark_file, sep="\t", header=0, dtype=numpy.object_)
        df = df[~df["mark"].isna()]
        for response_id, mark in zip(df["response_id"], df["mark"]):
            mark_lookups.setdefault(int(response_id), {})[label] = mark
    for response_id, marks in mark_lookups.items():
        if marks["ann1"] == "1b" or marks["ann2"] == "1b":
            marks["final"] = "1b"
        elif "corr" in marks:
            marks["final"] = marks["corr"]
        else:
            marks["final"] = str(min(int(marks["ann1"]), int(marks["ann2"])))

    miniexam_response_id = 0
    session_id = 0
    if not use_original_ids:
        pid = 0
    for participant in participants:
        if (
            (which == "complete" and participant.miniexam_finish_date is None) or
            (which == "incomplete" and participant.miniexam_finish_date is not None)
        ):
            continue
        if use_original_ids:
            pid = participant.id
        selfassess_sessions = get_participant_sessions(
            participant,
            only_selfassess=True
        )
        first_date = selfassess_sessions[0]["first_timestamp"].date() if selfassess_sessions else None
        miniexam_sessions = get_participant_sessions(
            participant,
            only_miniexam=True
        )
        miniexam_time_secs = int(sum((
            miniexam_session["time"].total_seconds()
            for miniexam_session
            in miniexam_sessions
        )) + 0.5)
        ddb_conn.execute(
            "insert into participant values (?, {} ?, ?, ?, ?, ?)".format(
                "?, " * len(CEFR_FIELDS)
            ),
            [
                pid,
                *(
                    getattr(participant, cefr_field)
                    for cefr_field
                    in CEFR_FIELDS
                ),
                participant.lived_in_finland,
                participant.proof_age.name,
                participant.proof_type.name,
                miniexam_time_secs,
                (participant.miniexam_finish_date.date() - first_date).days if participant.miniexam_finish_date else None
            ]
        )
        participant_languages = []
        for language in participant.languages:
            participant_languages.append((
                pid,
                language.language,
                language.level,
            ))
        ddb_conn.executemany(
            "insert into participant_language values (?, ?, ?)",
            participant_languages
        )
        response_vals = []
        word_rating = {}
        for selfassess_session in selfassess_sessions:
            session_date = selfassess_session["first_timestamp"].date()
            ddb_conn.execute(
                "insert into selfassess_session values (?, ?, ?, ?, ?)",
                [
                    session_id,
                    pid,
                    selfassess_session["device"],
                    int(selfassess_session["time"].total_seconds() + 0.5),
                    (session_date - first_date).days
                ]
            )
            for response in selfassess_session["response"]:
                if not getattr(response, "is_latest", False):
                    continue
                presentation_timestamp = response.slot.presentations[-1].timestamp
                rt = int((response.timestamp - presentation_timestamp) / timedelta(microseconds=1) + 0.5)
                response_vals.append((
                    session_id,
                    response.slot.word.word,
                    rt,
                    response.rating
                ))
            session_id += 1
        flush_rows("selfassess_response", ddb_conn, response_vals)
        miniexam_responses = []
        miniexam_marks = []
        for miniexam_slot in participant.miniexam_slots:
            latest_timestamp = None
            latest_response = None
            for response in miniexam_slot.responses:
                if (latest_timestamp is None
                        or response.timestamp > latest_timestamp):
                    latest_timestamp = response.timestamp
                    latest_response = response
            if not latest_response:
                continue
            miniexam_responses.append((
                miniexam_response_id,
                pid,
                miniexam_slot.word.word,
                latest_response.response_lang.name if latest_response.response_lang is not None else None,
                latest_response.response_type.name,
                latest_response.response,
                latest_response.mark
            ))
            for marker, mark in mark_lookups[latest_response.id].items():
                miniexam_marks.append((
                    miniexam_response_id, marker, mark
                ))
            miniexam_response_id += 1
        flush_rows("miniexam_response", ddb_conn, miniexam_responses)
        flush_rows("miniexam_mark", ddb_conn, miniexam_marks)
        if not use_original_ids:
            pid += 1


if __name__ == "__main__":
    main()
