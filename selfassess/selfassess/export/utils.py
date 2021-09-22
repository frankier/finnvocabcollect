import json
import user_agents
from statistics import mode
from selfassess.database import Presentation, Response, SessionLogEntry, SessionEvent


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


def gather_timestamped(objs):
    objs_timestamped = [
        (obj.timestamp, obj)
        for obj
        in objs
    ]
    if objs_timestamped:
        objs_timestamped[-1][1].is_latest = True
    return objs_timestamped


def get_participant_sessions(
    participant,
    only_selfassess=False,
    only_miniexam=False
):
    events = []
    for session_log_entry in participant.session_log_entries:
        if (
            (
                only_selfassess and
                session_log_entry.type not in (
                    SessionEvent.selfassess_hit,
                    SessionEvent.selfassess_focus,
                    SessionEvent.selfassess_blur,
                    SessionEvent.selfassess_input
                )
            )
            or
            (
                only_miniexam and
                session_log_entry.type not in (
                    SessionEvent.miniexam_blur,
                    SessionEvent.miniexam_focus,
                    SessionEvent.miniexam_input
                )
            )
        ):
            continue
        events.append((session_log_entry.timestamp, session_log_entry))
    if not only_miniexam:
        for slot in participant.response_slots:
            events.extend(gather_timestamped(slot.responses))
            events.extend(gather_timestamped(slot.presentations))
    events.sort()
    last_timestamp = None
    sessions = []

    def new_session():
        sessions.append({
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

    if not events:
        return sessions

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
            sessions[-1]["response"].append(event)
        elif isinstance(event, SessionLogEntry):
            device = ua_to_device(json.loads(event.payload)["user_agent"])
            sessions[-1]["devices"].append(device)
        last_timestamp = timestamp
    end_session(timestamp)
    return sessions


