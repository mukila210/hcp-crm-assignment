"""
The five LangGraph tools available to the HCP-interaction agent.
"""
from datetime import datetime
from typing import Optional

from langchain_core.tools import tool
from sqlalchemy.orm import Session

from app import models
from app.database import SessionLocal


@tool
def log_interaction_tool(
    hcp_id: str,
    field_rep_id: str,
    interaction_type: str,
    topics_discussed: list[str],
    materials_shared: Optional[list[str]] = None,
    hcp_sentiment: Optional[str] = None,
    next_best_action: Optional[str] = None,
    notes: Optional[str] = None,
) -> dict:
    """Create a new logged HCP interaction record."""
    db: Session = SessionLocal()
    try:
        interaction = models.Interaction(
            hcp_id=hcp_id,
            field_rep_id=field_rep_id,
            interaction_type=interaction_type,
            interaction_date=datetime.utcnow(),
            topics_discussed=topics_discussed,
            materials_shared=materials_shared or [],
            hcp_sentiment=hcp_sentiment,
            next_best_action=next_best_action,
            notes=notes,
            source=models.InteractionSource.CHAT_ASSISTANT,
        )
        db.add(interaction)
        db.commit()
        db.refresh(interaction)
        return {"status": "created", "interaction_id": interaction.id}
    finally:
        db.close()


@tool
def edit_interaction_tool(interaction_id: str, updates: dict) -> dict:
    """Modify fields on an already-logged interaction."""
    db: Session = SessionLocal()
    try:
        interaction = db.query(models.Interaction).filter(
            models.Interaction.id == interaction_id
        ).first()
        if not interaction:
            return {"status": "error", "message": "Interaction not found"}
        for field, value in updates.items():
            if hasattr(interaction, field):
                setattr(interaction, field, value)
        interaction.updated_at = datetime.utcnow()
        db.commit()
        return {"status": "updated", "interaction_id": interaction.id}
    finally:
        db.close()


@tool
def lookup_hcp_tool(hcp_id: str) -> dict:
    """Retrieve an HCP's profile and recent interaction history for agent context."""
    db: Session = SessionLocal()
    try:
        hcp = db.query(models.HCP).filter(models.HCP.id == hcp_id).first()
        if not hcp:
            return {"status": "not_found"}
        recent = (
            db.query(models.Interaction)
            .filter(models.Interaction.hcp_id == hcp_id)
            .order_by(models.Interaction.interaction_date.desc())
            .limit(3)
            .all()
        )
        return {
            "name": hcp.full_name,
            "specialty": hcp.specialty,
            "tier": hcp.tier,
            "recent_interaction_count": len(recent),
        }
    finally:
        db.close()


@tool
def flag_adverse_event_tool(interaction_id: str, summary: str) -> dict:
    """Mark an interaction as containing a potential adverse event for compliance review."""
    db: Session = SessionLocal()
    try:
        interaction = db.query(models.Interaction).filter(
            models.Interaction.id == interaction_id
        ).first()
        if not interaction:
            return {"status": "error", "message": "Interaction not found"}
        interaction.adverse_event_flag = True
        interaction.adverse_event_summary = summary
        db.commit()
        return {"status": "flagged", "interaction_id": interaction.id}
    finally:
        db.close()


@tool
def suggest_next_best_action_tool(topics_discussed: list[str], hcp_sentiment: str) -> str:
    """Suggest a concrete follow-up action based on what was discussed and how it landed."""
    if hcp_sentiment == "positive" and topics_discussed:
        return f"Send follow-up materials on {topics_discussed[0]} within 3 business days."
    if hcp_sentiment == "negative":
        return "Escalate to Medical Affairs for a scientific follow-up call before next visit."
    return "Schedule a check-in call in 2-3 weeks to reinforce key discussion points."


ALL_TOOLS = [
    log_interaction_tool,
    edit_interaction_tool,
    lookup_hcp_tool,
    flag_adverse_event_tool,
    suggest_next_best_action_tool,
]