from sqlalchemy import Column, DateTime, Enum, ForeignKey, func, Integer, String, JSON
from sqlalchemy.orm import declarative_base, relationship
import enum


Base = declarative_base()


class Participant(Base):
    __tablename__ = "participant"

    id = Column(Integer, primary_key=True)
    token = Column(String, nullable=False)
    create_date = Column(DateTime, nullable=False)
    accept_date = Column(DateTime)
    withdraw_date = Column(DateTime)
    email = Column(String, unique=True, nullable=False)
    given_name = Column(String)
    surname = Column(String)
    proof = Column(String)
    proof_upload_date = Column(DateTime)
    proof_accept_date = Column(DateTime)
    selfassess_start_date = Column(DateTime)
    selfassess_finish_date = Column(DateTime)
    miniexam_start_date = Column(DateTime)
    miniexam_finish_date = Column(DateTime)
    next_response = Column(Integer, default=0)

    response_slots = relationship("ResponseSlot", back_populates="participant")
    session_log_entries = relationship(
        "SessionLogEntry",
        back_populates="participant"
    )


class Word(Base):
    __tablename__ = "word"

    id = Column(Integer, primary_key=True)
    word = Column(String, unique=True, nullable=False)


class ResponseSlot(Base):
    __tablename__ = "response_slot"

    id = Column(Integer, primary_key=True)
    participant_id = Column(Integer, ForeignKey('participant.id'))
    word_id = Column(Integer, ForeignKey('word.id'))
    response_order = Column(Integer)

    participant = relationship("Participant", back_populates="response_slots")
    responses = relationship("Response", back_populates="slot")
    presentations = relationship("Presentation", back_populates="slot")


class Response(Base):
    __tablename__ = "response"

    id = Column(Integer, primary_key=True)
    response_slot_id = Column(Integer, ForeignKey('response_slot.id'))
    timestamp = Column(DateTime)
    rating = Column(Integer)

    slot = relationship("ResponseSlot", back_populates="responses")


class Presentation(Base):
    __tablename__ = "presentation"
    id = Column(Integer, primary_key=True)
    response_slot_id = Column(Integer, ForeignKey('response_slot.id'))
    timestamp = Column(DateTime)

    slot = relationship("ResponseSlot", back_populates="presentations")


class SessionEvent(enum.Enum):
    overview_hit = 1
    selfassess_hit = 2
    selfassess_focus = 3
    selfassess_blur = 4


class SessionLogEntry(Base):
    __tablename__ = "session_log_entry"

    id = Column(Integer, primary_key=True)
    participant_id = Column(Integer, ForeignKey('participant.id'))
    type = Column(Enum(SessionEvent))
    payload = Column(JSON)

    participant = relationship(
        "Participant",
        back_populates="session_log_entries"
    )
