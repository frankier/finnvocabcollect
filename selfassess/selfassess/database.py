from sqlalchemy import (
    Column, Date, DateTime, Enum, ForeignKey, func, Integer, String, JSON
)
from sqlalchemy.orm import declarative_base, relationship
import enum
from .quali import ProofType, ProofAge, CEFR_LEVELS
from wtforms import RadioField, TextAreaField


Base = declarative_base()
CEFR_INFO = {
    "form_field_class": RadioField,
    "choices": list(enumerate(
        (
            f"CEFR {cefr.upper()} / YKI {yki}"
            for yki, cefr
            in enumerate(CEFR_LEVELS, start=1)
        ),
        start=1
    ))
}


class Participant(Base):
    __tablename__ = "participant"

    id = Column(Integer, primary_key=True)
    token = Column(String, nullable=False)
    create_date = Column(DateTime, nullable=False)
    accept_date = Column(DateTime)
    accept_deadline = Column(Date, nullable=False)
    withdraw_date = Column(DateTime)
    email = Column(String, unique=True, nullable=False)
    given_name = Column(String, info={"label": "Given name"})
    surname = Column(String, info={"label": "Surname"})
    proof = Column(String)
    proof_upload_date = Column(DateTime)
    proof_accept_date = Column(DateTime)
    proof_type = Column(Enum(ProofType), nullable=False, info={"label": "Type of proof"})
    proof_age = Column(Enum(ProofAge), nullable=False, info={"label": "Age of proof"})
    cefr_proof_speaking = Column(Integer, info=CEFR_INFO)
    cefr_proof_writing = Column(Integer, info=CEFR_INFO)
    cefr_proof_listening_comprehension = Column(Integer, info=CEFR_INFO)
    cefr_proof_reading_comprehension = Column(Integer, info=CEFR_INFO)
    cefr_selfassess_speaking = Column(Integer, info=CEFR_INFO)
    cefr_selfassess_writing = Column(Integer, info=CEFR_INFO)
    cefr_selfassess_listening_comprehension = Column(Integer, info=CEFR_INFO)
    cefr_selfassess_reading_comprehension = Column(Integer, info=CEFR_INFO)
    text_on_proof = Column(String, nullable=False, default="", info={"form_field_class": TextAreaField})
    selfassess_start_date = Column(DateTime)
    selfassess_finish_date = Column(DateTime)
    selfassess_accept_date = Column(DateTime)
    miniexam_start_date = Column(DateTime)
    miniexam_finish_date = Column(DateTime)
    miniexam_accept_date = Column(DateTime)
    complete_deadline = Column(Date, nullable=False)
    next_response = Column(Integer, default=0)

    response_slots = relationship(
        "ResponseSlot",
        back_populates="participant",
        order_by="ResponseSlot.response_order"
    )
    miniexam_slots = relationship(
        "MiniexamSlot",
        back_populates="participant",
        order_by="MiniexamSlot.miniexam_order"
    )
    session_log_entries = relationship(
        "SessionLogEntry",
        back_populates="participant"
    )
    languages = relationship(
        "ParticipantLanguage",
        back_populates="participant"
    )


class ParticipantLanguage(Base):
    __tablename__ = "participant_language"

    id = Column(Integer, primary_key=True)
    participant_id = Column(Integer, ForeignKey('participant.id'), nullable=False)
    language = Column(String, nullable=False)
    level = Column(String, nullable=False)

    participant = relationship("Participant", back_populates="languages")


class Word(Base):
    __tablename__ = "word"

    id = Column(Integer, primary_key=True)
    word = Column(String, unique=True, nullable=False)

    response_slots = relationship("ResponseSlot", back_populates="word")
    miniexam_slots = relationship("MiniexamSlot", back_populates="word")


class ResponseSlot(Base):
    __tablename__ = "response_slot"

    id = Column(Integer, primary_key=True)
    participant_id = Column(Integer, ForeignKey('participant.id'), nullable=False)
    word_id = Column(Integer, ForeignKey('word.id'), nullable=False)
    response_order = Column(Integer, nullable=False)

    participant = relationship("Participant", back_populates="response_slots")
    responses = relationship("Response", back_populates="slot", order_by="Response.timestamp")
    presentations = relationship("Presentation", back_populates="slot")
    word = relationship("Word", back_populates="response_slots")


class Response(Base):
    __tablename__ = "response"

    id = Column(Integer, primary_key=True)
    response_slot_id = Column(Integer, ForeignKey('response_slot.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    rating = Column(Integer, nullable=False)

    slot = relationship("ResponseSlot", back_populates="responses")

    def __repr__(self):
        return f"<Response @{self.timestamp!r}>"


class Presentation(Base):
    __tablename__ = "presentation"
    id = Column(Integer, primary_key=True)
    response_slot_id = Column(Integer, ForeignKey('response_slot.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False)

    slot = relationship("ResponseSlot", back_populates="presentations")


class MiniexamSlot(Base):
    __tablename__ = "miniexam_slot"

    id = Column(Integer, primary_key=True)
    participant_id = Column(Integer, ForeignKey('participant.id'), nullable=False)
    word_id = Column(Integer, ForeignKey('word.id'), nullable=False)
    miniexam_order = Column(Integer, nullable=False)

    participant = relationship("Participant", back_populates="miniexam_slots")
    responses = relationship("MiniexamResponse", back_populates="slot", order_by="MiniexamResponse.timestamp")
    word = relationship("Word", back_populates="miniexam_slots")


@enum.unique
class MiniexamResponseLanguage(enum.Enum):
    en = 1
    hu = 2
    ru = 3


@enum.unique
class MiniexamResponseType(enum.Enum):
    trans_defn = 1
    topic = 2
    donotknow = 3


class MiniexamResponse(Base):
    __tablename__ = "miniexam_response"

    id = Column(Integer, primary_key=True)
    miniexam_slot_id = Column(Integer, ForeignKey('miniexam_slot.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    response_lang = Column(Enum(MiniexamResponseLanguage), nullable=True)
    response_type = Column(Enum(MiniexamResponseType), nullable=False)
    response = Column(String, nullable=False)
    mark = Column(Integer)

    slot = relationship("MiniexamSlot", back_populates="responses")


@enum.unique
class SessionEvent(enum.Enum):
    overview_hit = 1
    selfassess_hit = 2
    selfassess_focus = 3
    selfassess_blur = 4
    miniexam_focus = 5
    miniexam_blur = 6
    miniexam_input = 7
    selfassess_input = 8


class SessionLogEntry(Base):
    __tablename__ = "session_log_entry"

    id = Column(Integer, primary_key=True)
    participant_id = Column(Integer, ForeignKey('participant.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    type = Column(Enum(SessionEvent), nullable=False)
    payload = Column(JSON)

    participant = relationship(
        "Participant",
        back_populates="session_log_entries"
    )
