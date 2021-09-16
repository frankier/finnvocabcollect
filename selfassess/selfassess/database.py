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
    selfassess_accept_date = Column(DateTime)
    miniexam_start_date = Column(DateTime)
    miniexam_finish_date = Column(DateTime)
    miniexam_accept_date = Column(DateTime)
    next_response = Column(Integer, default=0)

    response_slots = relationship("ResponseSlot", back_populates="participant")
    miniexam_slots = relationship("MiniexamSlot", back_populates="participant")
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
    response_order = Column(Integer)

    participant = relationship("Participant", back_populates="response_slots")
    responses = relationship("Response", back_populates="slot")
    presentations = relationship("Presentation", back_populates="slot")
    word = relationship("Word", back_populates="response_slots")


class Response(Base):
    __tablename__ = "response"

    id = Column(Integer, primary_key=True)
    response_slot_id = Column(Integer, ForeignKey('response_slot.id'), nullable=False)
    timestamp = Column(DateTime)
    rating = Column(Integer)

    slot = relationship("ResponseSlot", back_populates="responses")

    def __repr__(self):
        return f"<Response @{self.timestamp!r}>"


class Presentation(Base):
    __tablename__ = "presentation"
    id = Column(Integer, primary_key=True)
    response_slot_id = Column(Integer, ForeignKey('response_slot.id'), nullable=False)
    timestamp = Column(DateTime)

    slot = relationship("ResponseSlot", back_populates="presentations")


class MiniexamSlot(Base):
    __tablename__ = "miniexam_slot"

    id = Column(Integer, primary_key=True)
    participant_id = Column(Integer, ForeignKey('participant.id'), nullable=False)
    word_id = Column(Integer, ForeignKey('word.id'), nullable=False)
    miniexam_order = Column(Integer)

    participant = relationship("Participant", back_populates="miniexam_slots")
    responses = relationship("MiniexamResponse", back_populates="slot")
    word = relationship("Word", back_populates="miniexam_slots")


class MiniexamResponseLanguage(enum.Enum):
    en = 1
    hu = 2
    ru = 3


class MiniexamResponseType(enum.Enum):
    trans_defn = 1
    topic = 2
    donotknow = 3


class MiniexamResponse(Base):
    __tablename__ = "miniexam_response"

    id = Column(Integer, primary_key=True)
    miniexam_slot_id = Column(Integer, ForeignKey('miniexam_slot.id'), nullable=False)
    timestamp = Column(DateTime)
    response_lang = Column(Enum(MiniexamResponseLanguage), nullable=True)
    response_type = Column(Enum(MiniexamResponseType))
    response = Column(String, nullable=False)

    slot = relationship("MiniexamSlot", back_populates="responses")


class SessionEvent(enum.Enum):
    overview_hit = 1
    selfassess_hit = 2
    selfassess_focus = 3
    selfassess_blur = 4
    miniexam_focus = 3
    miniexam_blur = 4


class SessionLogEntry(Base):
    __tablename__ = "session_log_entry"

    id = Column(Integer, primary_key=True)
    participant_id = Column(Integer, ForeignKey('participant.id'), nullable=False)
    timestamp = Column(DateTime)
    type = Column(Enum(SessionEvent))
    payload = Column(JSON)

    participant = relationship(
        "Participant",
        back_populates="session_log_entries"
    )
