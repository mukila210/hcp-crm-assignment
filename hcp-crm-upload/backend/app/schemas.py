from datetime import datetime
from typing import List, Optional, Literal

from pydantic import BaseModel, Field


class SampleDrop(BaseModel):
    product: str
    quantity: int
    lot_number: Optional[str] = None


class InteractionBase(BaseModel):
    hcp_id: str
    field_rep_id: str
    interaction_type: Literal[
        "in_person_visit", "virtual_call", "phone_call", "email", "conference", "sample_drop"
    ]
    interaction_date: datetime
    duration_minutes: Optional[str] = None
    topics_discussed: List[str] = Field(default_factory=list)
    materials_shared: List[str] = Field(default_factory=list)
    samples_dropped: List[SampleDrop] = Field(default_factory=list)
    hcp_sentiment: Optional[Literal["positive", "neutral", "negative"]] = None
    next_best_action: Optional[str] = None
    notes: Optional[str] = None


class InteractionCreate(InteractionBase):
    """Used by the structured-form submission path."""
    pass


class InteractionResponse(InteractionBase):
    id: str
    adverse_event_flag: bool
    adverse_event_summary: Optional[str] = None
    off_label_flag: bool
    source: str
    ai_confidence: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ---- Chat / agent contracts ----

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatTurnRequest(BaseModel):
    session_id: str
    field_rep_id: str
    message: str
    history: List[ChatMessage] = Field(default_factory=list)


class ChatTurnResponse(BaseModel):
    session_id: str
    assistant_message: str
    # Populated once the agent believes it has enough info to log the interaction
    draft_interaction: Optional[dict] = None
    is_ready_to_confirm: bool = False
    requires_escalation: bool = False   # true if an adverse event / off-label mention was detected
