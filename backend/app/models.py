"""Database models for the HCP CRM module."""
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class HCP(Base):
    """A Healthcare Professional the field rep interacts with."""

    __tablename__ = "hcps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    specialty: Mapped[str] = mapped_column(String(120), default="")
    institution: Mapped[str] = mapped_column(String(200), default="")
    email: Mapped[str] = mapped_column(String(200), default="")

    interactions: Mapped[list["Interaction"]] = relationship(
        back_populates="hcp", cascade="all, delete-orphan"
    )


class Interaction(Base):
    """A single logged interaction with an HCP."""

    __tablename__ = "interactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hcp_id: Mapped[int | None] = mapped_column(ForeignKey("hcps.id"), nullable=True)
    hcp_name: Mapped[str] = mapped_column(String(200), default="")

    interaction_type: Mapped[str] = mapped_column(String(60), default="Meeting")
    date: Mapped[str] = mapped_column(String(20), default="")  # YYYY-MM-DD
    time: Mapped[str] = mapped_column(String(20), default="")  # HH:MM

    attendees: Mapped[list] = mapped_column(JSON, default=list)
    topics_discussed: Mapped[str] = mapped_column(Text, default="")
    materials_shared: Mapped[list] = mapped_column(JSON, default=list)
    samples_distributed: Mapped[list] = mapped_column(JSON, default=list)

    sentiment: Mapped[str] = mapped_column(String(20), default="Neutral")
    outcomes: Mapped[str] = mapped_column(Text, default="")
    follow_up_actions: Mapped[str] = mapped_column(Text, default="")

    ai_summary: Mapped[str] = mapped_column(Text, default="")
    ai_suggested_followups: Mapped[list] = mapped_column(JSON, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow
    )

    hcp: Mapped["HCP"] = relationship(back_populates="interactions")
    follow_ups: Mapped[list["FollowUp"]] = relationship(
        back_populates="interaction", cascade="all, delete-orphan"
    )


class FollowUp(Base):
    """A scheduled follow-up task tied to an HCP / interaction."""

    __tablename__ = "follow_ups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    interaction_id: Mapped[int | None] = mapped_column(
        ForeignKey("interactions.id"), nullable=True
    )
    hcp_id: Mapped[int | None] = mapped_column(ForeignKey("hcps.id"), nullable=True)
    hcp_name: Mapped[str] = mapped_column(String(200), default="")

    description: Mapped[str] = mapped_column(Text, default="")
    due_date: Mapped[str] = mapped_column(String(20), default="")  # YYYY-MM-DD
    status: Mapped[str] = mapped_column(String(20), default="pending")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    interaction: Mapped["Interaction"] = relationship(back_populates="follow_ups")
