import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Text, DateTime, ForeignKey, Enum, Boolean, JSON
)
# from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())
    # return String(64)


class InteractionType(str, enum.Enum):
    IN_PERSON_VISIT = "in_person_visit"
    VIRTUAL_CALL = "virtual_call"
    PHONE_CALL = "phone_call"
    EMAIL = "email"
    CONFERENCE = "conference"
    SAMPLE_DROP = "sample_drop"


class InteractionSource(str, enum.Enum):
    STRUCTURED_FORM = "structured_form"
    CHAT_ASSISTANT = "chat_assistant"


class Sentiment(str, enum.Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class FieldRep(Base):
    __tablename__ = "field_reps"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    name = Column(String(120), nullable=False)
    email = Column(String(160), unique=True, nullable=False)
    territory = Column(String(120))

    interactions = relationship("Interaction", back_populates="field_rep")


class HCP(Base):
    """Healthcare Professional master record."""
    __tablename__ = "hcps"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    full_name = Column(String(160), nullable=False)
    npi_id = Column(String(20), unique=True, index=True)  # National Provider Identifier
    specialty = Column(String(120))
    institution = Column(String(200))
    city = Column(String(120))
    preferred_channel = Column(String(50))  # e.g. in_person, virtual, email
    tier = Column(String(20))  # e.g. KOL / high-value / standard, drives call frequency

    interactions = relationship("Interaction", back_populates="hcp")


class Interaction(Base):
    """A single logged interaction between a field rep and an HCP."""
    __tablename__ = "interactions"

    id = Column(String(64), primary_key=True, default=gen_uuid)
    hcp_id = Column(String(64), ForeignKey("hcps.id"), nullable=False)
    field_rep_id = Column(String(64), ForeignKey("field_reps.id"), nullable=False)

    interaction_type = Column(Enum(InteractionType), nullable=False)
    interaction_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    duration_minutes = Column(String(10))

    topics_discussed = Column(JSON)          # list[str] e.g. ["Drug X efficacy", "New indication"]
    materials_shared = Column(JSON)          # list[str] e.g. ["Leave-behind brochure v3"]
    samples_dropped = Column(JSON)           # list[{product, quantity, lot_number}]
    hcp_sentiment = Column(Enum(Sentiment))
    next_best_action = Column(Text)          # AI-suggested or rep-entered follow-up
    notes = Column(Text)

    # Compliance / safety
    adverse_event_flag = Column(Boolean, default=False)
    adverse_event_summary = Column(Text, nullable=True)
    off_label_flag = Column(Boolean, default=False)

    # Provenance
    source = Column(Enum(InteractionSource), nullable=False, default=InteractionSource.STRUCTURED_FORM)
    raw_transcript = Column(Text, nullable=True)   # full chat transcript if logged conversationally
    ai_confidence = Column(String(10), nullable=True)  # 0-1, agent's confidence in the extraction

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    hcp = relationship("HCP", back_populates="interactions")
    field_rep = relationship("FieldRep", back_populates="interactions")
