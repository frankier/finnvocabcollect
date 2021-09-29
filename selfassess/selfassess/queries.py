import quart.flask_patch  # noqa
from .database import Response, ResponseSlot, ParticipantLanguage
from sqlalchemy import select, desc, func
from sqlalchemy.orm import contains_eager, joinedload, aliased


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
