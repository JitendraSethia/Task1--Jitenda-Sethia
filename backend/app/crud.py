"""Database access helpers shared by REST routers and LangGraph tools."""
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from . import models


# ------------------------------ HCP ------------------------------
def list_hcps(db: Session, query: str = "") -> list[models.HCP]:
    stmt = select(models.HCP)
    if query:
        like = f"%{query}%"
        stmt = stmt.where(
            or_(models.HCP.name.ilike(like), models.HCP.specialty.ilike(like))
        )
    return list(db.scalars(stmt.order_by(models.HCP.name)))


def get_hcp_by_name(db: Session, name: str) -> models.HCP | None:
    if not name:
        return None
    return db.scalars(
        select(models.HCP).where(models.HCP.name.ilike(f"%{name}%"))
    ).first()


def get_or_create_hcp(db: Session, name: str) -> models.HCP | None:
    if not name:
        return None
    hcp = get_hcp_by_name(db, name)
    if hcp:
        return hcp
    hcp = models.HCP(name=name.strip())
    db.add(hcp)
    db.flush()
    return hcp


# -------------------------- Interaction --------------------------
def create_interaction(db: Session, data: dict) -> models.Interaction:
    payload = dict(data)
    # Resolve / attach an HCP record when a name is supplied.
    name = payload.get("hcp_name") or ""
    if name and not payload.get("hcp_id"):
        hcp = get_or_create_hcp(db, name)
        if hcp:
            payload["hcp_id"] = hcp.id
            payload["hcp_name"] = hcp.name

    interaction = models.Interaction(**payload)
    db.add(interaction)
    db.commit()
    db.refresh(interaction)
    return interaction


def get_interaction(db: Session, interaction_id: int) -> models.Interaction | None:
    return db.get(models.Interaction, interaction_id)


def list_interactions(
    db: Session, hcp_name: str = "", limit: int = 50
) -> list[models.Interaction]:
    stmt = select(models.Interaction)
    if hcp_name:
        stmt = stmt.where(models.Interaction.hcp_name.ilike(f"%{hcp_name}%"))
    stmt = stmt.order_by(models.Interaction.created_at.desc()).limit(limit)
    return list(db.scalars(stmt))


def update_interaction(
    db: Session, interaction_id: int, patch: dict
) -> models.Interaction | None:
    interaction = get_interaction(db, interaction_id)
    if not interaction:
        return None
    for key, value in patch.items():
        if value is not None and hasattr(interaction, key):
            setattr(interaction, key, value)
    db.commit()
    db.refresh(interaction)
    return interaction


def latest_interaction_for_hcp(
    db: Session, hcp_name: str
) -> models.Interaction | None:
    return db.scalars(
        select(models.Interaction)
        .where(models.Interaction.hcp_name.ilike(f"%{hcp_name}%"))
        .order_by(models.Interaction.created_at.desc())
    ).first()


# --------------------------- Follow-up ---------------------------
def create_follow_up(db: Session, data: dict) -> models.FollowUp:
    follow_up = models.FollowUp(**data)
    db.add(follow_up)
    db.commit()
    db.refresh(follow_up)
    return follow_up


def list_follow_ups(db: Session, hcp_name: str = "") -> list[models.FollowUp]:
    stmt = select(models.FollowUp)
    if hcp_name:
        stmt = stmt.where(models.FollowUp.hcp_name.ilike(f"%{hcp_name}%"))
    return list(db.scalars(stmt.order_by(models.FollowUp.created_at.desc())))
