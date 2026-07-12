from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.agent.graph import interaction_agent

router = APIRouter(prefix="/api/chat", tags=["chat"])

# In-memory session store for demo purposes.
# Swap for Redis (or LangGraph's built-in checkpointer with a Postgres saver) in production.
_SESSIONS: dict[str, dict] = {}


@router.post("/turn", response_model=schemas.ChatTurnResponse)
def chat_turn(payload: schemas.ChatTurnRequest):
    session = _SESSIONS.get(payload.session_id, {"messages": [], "slots": {}})
    session["messages"].append({"role": "user", "content": payload.message})

    result = interaction_agent.invoke(session)
    _SESSIONS[payload.session_id] = result

    return schemas.ChatTurnResponse(
        session_id=payload.session_id,
        assistant_message=result["assistant_message"],
        draft_interaction=result.get("slots") or None,
        is_ready_to_confirm=result.get("is_ready_to_confirm", False),
        requires_escalation=result.get("adverse_event_flag", False),
    )


@router.post("/{session_id}/confirm", response_model=schemas.InteractionResponse, status_code=201)
def confirm_interaction(
    session_id: str,
    hcp_id: str,
    field_rep_id: str,
    db: Session = Depends(get_db),
):
    """Rep taps 'Confirm & Save' after reviewing the AI-drafted summary."""
    session = _SESSIONS.get(session_id)
    if not session:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Chat session not found or expired")

    slots = session["slots"]
    transcript = "\n".join(f"{m['role']}: {m['content']}" for m in session["messages"])

    interaction = models.Interaction(
        hcp_id=hcp_id,
        field_rep_id=field_rep_id,
        interaction_type=slots.get("interaction_type", "in_person_visit"),
        interaction_date=slots.get("interaction_date") or __import__("datetime").datetime.utcnow(),
        topics_discussed=slots.get("topics_discussed", []),
        materials_shared=slots.get("materials_shared", []),
        samples_dropped=slots.get("samples_dropped", []),
        hcp_sentiment=slots.get("hcp_sentiment"),
        next_best_action=slots.get("next_best_action"),
        adverse_event_flag=session.get("adverse_event_flag", False),
        adverse_event_summary=session.get("adverse_event_summary"),
        off_label_flag=session.get("off_label_flag", False),
        source=models.InteractionSource.CHAT_ASSISTANT,
        raw_transcript=transcript,
        ai_confidence=str(session.get("confidence", "")),
    )
    db.add(interaction)
    db.commit()
    db.refresh(interaction)

    del _SESSIONS[session_id]
    return interaction
