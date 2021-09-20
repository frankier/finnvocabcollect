import json
import user_agents
from statistics import mode
from selfassess.database import Response, SessionLogEntry


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
            sessions[-1]["has_selfassess"] = True
            sessions[-1]["response"].append(event)
        elif isinstance(event, SessionLogEntry):
            device = ua_to_device(json.loads(event.payload)["user_agent"])
            sessions[-1]["devices"].append(device)
        last_timestamp = timestamp
    end_session(timestamp)
    return sessions


