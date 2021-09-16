import click
import duckdb
import orjson
import user_agents
from statistics import mode
from selfassess.utils import get_session
from selfassess.database import Participant, Response, SessionLogEntry


def setup_duckdb(db_out):
    conn = duckdb.connect(db_out)

    print("Creating tables")
    conn.execute("""
    create table participant (
        id int primary key
    );
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


SESSION_TIMEOUT = 300


def ua_to_device(ua):
    ua_parse = user_agents.parse(ua)
    if ua_parse.is_tablet:
        return "tablet"
    elif ua_parse.is_mobile:
        return "mobile"
    elif ua_parse.is_pc:
        return "pc"
    else:
        return "unknown"


def get_participant_sessions(participant):
    events = []
    for session_log_entry in participant.session_log_entries:
        events.append((session_log_entry.timestamp, session_log_entry))
    for slot in participant.response_slots:
        latest_timestamp = None
        responses = []
        for response in slot.responses:
            if (latest_timestamp is None
                    or response.timestamp > latest_timestamp):
                latest_timestamp = response.timestamp
            responses.append((response.timestamp, response))
        for timestamp, response in responses:
            response.is_latest = timestamp == latest_timestamp
        events.extend(responses)
        for presentation in slot.presentations:
            events.append((presentation.timestamp, presentation))
    events.sort()
    last_timestamp = None
    sessions = []

    def new_session():
        sessions.append({
            "has_selfassess": False,
            "response": [],
            "devices": [],
            "first_timestamp": None,
            "time": None,
        })

    def end_session(timestamp):
        sessions[-1]["time"] = (timestamp - sessions[-1]["first_timestamp"])
        if sessions[-1]["devices"]:
            device = mode(sessions[-1]["devices"])
        else:
            device = "unknown"
        sessions[-1]["device"] = device
        sessions[-1]["last_timestamp"] = last_timestamp

    new_session()
    for timestamp, event in events:
        if (
            last_timestamp is not None
            and (timestamp - last_timestamp).total_seconds() > SESSION_TIMEOUT
        ):
            end_session(last_timestamp)
            new_session()
        if sessions[-1]["first_timestamp"] is None:
            sessions[-1]["first_timestamp"] = timestamp
        if isinstance(event, Response):
            sessions[-1]["has_selfassess"] = True
            sessions[-1]["response"].append(event)
        elif isinstance(event, SessionLogEntry):
            device = ua_to_device(orjson.loads(event.payload)["user_agent"])
            sessions[-1]["devices"].append(device)
        last_timestamp = timestamp
    end_session(timestamp)
    return sessions


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
        ddb_conn.execute("insert into participant values (?)", [pid])
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
