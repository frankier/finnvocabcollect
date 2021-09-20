import click
import duckdb
from selfassess.utils import get_session
from selfassess.database import Participant
from selfassess.quali import CEFR_SKILLS
from .utils import get_participant_sessions


CEFR_FIELDS = [
    f"cefr_{type}_{skill}"
    for type in ("selfassess", "proof")
    for skill in CEFR_SKILLS
]


PARTICIPANT_TABLE = """
create table participant (
    id int primary key,
    {}
    proof_age varchar,
    proof_type varchar
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
        level varchar
    );
    create table selfassess_session (
        id int primary key,
        participant_id int,
        device varchar,
        time_secs int
    );
    create table selfassess_response (
        session_id int,
        word varchar,
        time_secs int,
        grade int
    );
    create table miniexam_response (
        participant_id int,
        word varchar,
        type varchar,
        lang varchar,
        response varchar,
        grade int
    );
    """)
    return conn


@click.command()
@click.argument("db_out", type=click.Path())
@click.option(
    "--which",
    type=click.Choice(["all", "complete", "incomplete"]),
    default="all"
)
def main(db_out, which):
    # Inefficient ORM usage here
    # -- but there are 15 items and this runs as a batch job
    ddb_conn = setup_duckdb(db_out)
    sqlite_sess = get_session()
    participants = sqlite_sess.query(Participant)
    session_id = 0
    for pid, participant in enumerate(participants):
        if (
            (which == "complete" and participant.miniexam_finish_date is None) or
            (which == "incomplete" and participant.miniexam_finish_date is not None)
        ):
            continue
        ddb_conn.execute(
            "insert into participant values (?, {} ?, ?)".format(
                "?, " * len(CEFR_FIELDS)
            ),
            [
                pid,
                *(
                    getattr(participant, cefr_field)
                    for cefr_field
                    in CEFR_FIELDS
                ),
                participant.proof_age.name,
                participant.proof_type.name
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
        part_sessions = get_participant_sessions(participant)
        for part_session in part_sessions:
            if not part_session["has_selfassess"]:
                continue
            ddb_conn.execute(
                "insert into selfassess_session values (?, ?, ?, ?)",
                [
                    session_id,
                    pid,
                    part_session["device"],
                    int(part_session["time"].total_seconds() + 0.5)
                ]
            )
            response_vals = []
            for response in part_session["response"]:
                if not response.is_latest:
                    continue
                # TODO get reaction time using response.slot.presentations
                response_vals.append((
                    session_id,
                    response.slot.word.word,
                    1,
                    response.rating
                ))
            session_id += 1
            ddb_conn.executemany(
                "insert into selfassess_response values (?, ?, ?, ?)",
                response_vals
            )
        miniexam_responses = []
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
            # TODO: figure out how to grade and transfer grade here
            miniexam_responses.append((
                pid,
                miniexam_slot.word.word,
                latest_response.response_lang.name if latest_response.response_lang is not None else None,
                latest_response.response_type.name,
                latest_response.response,
                0
            ))
        ddb_conn.executemany(
            "insert into miniexam_response values (?, ?, ?, ?, ?, ?)",
            miniexam_responses
        )


if __name__ == "__main__":
    main()