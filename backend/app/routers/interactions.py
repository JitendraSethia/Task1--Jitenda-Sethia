"""REST endpoints backing the structured Log Interaction form."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import ai_service, crud, schemas
from ..database import get_db

router = APIRouter(prefix="/api", tags=["interactions"])


# ------------------------------- HCPs -------------------------------
@router.get("/hcps", response_model=list[schemas.HCPRead])
def get_hcps(q: str = Query("", description="search text"), db: Session = Depends(get_db)):
    return crud.list_hcps(db, query=q)


# --------------------------- Interactions ---------------------------
@router.post("/interactions", response_model=schemas.InteractionRead, status_code=201)
def create_interaction(payload: schemas.InteractionCreate, db: Session = Depends(get_db)):
    return crud.create_interaction(db, payload.model_dump())


@router.get("/interactions", response_model=list[schemas.InteractionRead])
def list_interactions(
    hcp_name: str = Query(""), limit: int = Query(50), db: Session = Depends(get_db)
):
    return crud.list_interactions(db, hcp_name=hcp_name, limit=limit)


@router.get("/interactions/{interaction_id}", response_model=schemas.InteractionRead)
def get_interaction(interaction_id: int, db: Session = Depends(get_db)):
    interaction = crud.get_interaction(db, interaction_id)
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return interaction


@router.put("/interactions/{interaction_id}", response_model=schemas.InteractionRead)
def update_interaction(
    interaction_id: int,
    payload: schemas.InteractionUpdate,
    db: Session = Depends(get_db),
):
    updated = crud.update_interaction(
        db, interaction_id, payload.model_dump(exclude_unset=True)
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return updated


# ------------------------------ AI helpers --------------------------
@router.post("/ai/summarize", response_model=schemas.SummarizeResponse)
def summarize(payload: schemas.SummarizeRequest):
    """Turn a free-text note / voice-note transcript into structured form fields."""
    data = ai_service.summarize_interaction(payload.text, payload.hcp_name)
    return schemas.SummarizeResponse(**data)


@router.post("/ai/suggest-followups", response_model=schemas.SuggestFollowupsResponse)
def suggest_followups(payload: schemas.SuggestFollowupsRequest):
    suggestions = ai_service.suggest_followups(
        hcp_name=payload.hcp_name,
        topics_discussed=payload.topics_discussed,
        outcomes=payload.outcomes,
        sentiment=payload.sentiment,
    )
    return schemas.SuggestFollowupsResponse(suggestions=suggestions)


# ------------------------------ Follow-ups --------------------------
@router.get("/follow-ups", response_model=list[schemas.FollowUpRead])
def list_follow_ups(hcp_name: str = Query(""), db: Session = Depends(get_db)):
    return crud.list_follow_ups(db, hcp_name=hcp_name)
