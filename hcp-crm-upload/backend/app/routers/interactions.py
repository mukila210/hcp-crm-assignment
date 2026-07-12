from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/api/interactions", tags=["interactions"])


@router.post("", response_model=schemas.InteractionResponse, status_code=201)
def create_interaction(payload: schemas.InteractionCreate, db: Session = Depends(get_db)):
    hcp = db.query(models.HCP).filter(models.HCP.id == payload.hcp_id).first()
    if not hcp:
        raise HTTPException(status_code=404, detail="HCP not found")

    interaction = models.Interaction(
        hcp_id=payload.hcp_id,
        field_rep_id=payload.field_rep_id,
        interaction_type=payload.interaction_type,
        interaction_date=payload.interaction_date,
        duration_minutes=payload.duration_minutes,
        topics_discussed=payload.topics_discussed,
        materials_shared=payload.materials_shared,
        samples_dropped=[s.model_dump() for s in payload.samples_dropped],
        hcp_sentiment=payload.hcp_sentiment,
        next_best_action=payload.next_best_action,
        notes=payload.notes,
        source=models.InteractionSource.STRUCTURED_FORM,
    )
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    return interaction


@router.get("", response_model=list[schemas.InteractionResponse])
def list_interactions(hcp_id: str | None = None, db: Session = Depends(get_db)):
    query = db.query(models.Interaction)
    if hcp_id:
        query = query.filter(models.Interaction.hcp_id == hcp_id)
    return query.order_by(models.Interaction.interaction_date.desc()).all()


@router.get("/{interaction_id}", response_model=schemas.InteractionResponse)
def get_interaction(interaction_id: str, db: Session = Depends(get_db)):
    interaction = db.query(models.Interaction).filter(models.Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return interaction
