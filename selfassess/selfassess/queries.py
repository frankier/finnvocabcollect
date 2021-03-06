import quart.flask_patch  # noqa
from .database import Response, ResponseSlot, ParticipantLanguage, Participant
from sqlalchemy import select, desc, func
from sqlalchemy.orm import contains_eager, joinedload, aliased, lazyload


def _recent_responses():
    subq = select(
        Response,
        func.row_number().over(
            partition_by=Response.response_slot_id,
            order_by=desc(Response.timestamp)
        ).label("rownb")
    )
    subq = subq.subquery(name="subq")
    aliased_responses = aliased(Response, alias=subq)
    return subq, aliased_responses


def recent_responses():
    subq, aliased_responses = _recent_responses()
    return (
        select(aliased_responses)
        .options(joinedload(aliased_responses.slot))
        .filter(subq.c.rownb == 1)
    )


def recent_responses_for_participant(participant):
    subq, aliased_responses = _recent_responses()
    return (
        select(aliased_responses)
        .join(aliased_responses.slot)
        .options(contains_eager(aliased_responses.slot))
        .filter(ResponseSlot.participant_id == participant.id)
        .filter(subq.c.rownb == 1)
    )


def native_language(user):
    return select(ParticipantLanguage).filter(
        ParticipantLanguage.primary_native.is_(True) &
        (ParticipantLanguage.participant_id == user.id)
    )


def latest_selfassess_response(user):
    return (
        select(func.max(Response.timestamp).label("latest_timestamp"))
        .join(ResponseSlot, Response.response_slot_id == ResponseSlot.id)
        .filter(
            ResponseSlot.participant_id == user.id
        )
    )


def participant_timeline_query():
    return select(Participant).options(
        lazyload(Participant.response_slots).options(
            joinedload(ResponseSlot.responses),
            joinedload(ResponseSlot.presentations)
        ),
        lazyload(Participant.session_log_entries)
    )
