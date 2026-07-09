"""Pydantic request/response schemas."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ----------------------------- HCP -----------------------------
class HCPRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    specialty: str = ""
    institution: str = ""
    email: str = ""


# -------------------------- Interaction ------------------------
class InteractionBase(BaseModel):
    hcp_id: int | None = None
    hcp_name: str = ""
    interaction_type: str = "Meeting"
    date: str = ""
    time: str = ""
    attendees: list[str] = Field(default_factory=list)
    topics_discussed: str = ""
    materials_shared: list[str] = Field(default_factory=list)
    samples_distributed: list[str] = Field(default_factory=list)
    sentiment: str = "Neutral"
    outcomes: str = ""
    follow_up_actions: str = ""


class InteractionCreate(InteractionBase):
    pass


class InteractionUpdate(BaseModel):
    """All fields optional so the UI / agent can patch selectively."""

    hcp_id: int | None = None
    hcp_name: str | None = None
    interaction_type: str | None = None
    date: str | None = None
    time: str | None = None
    attendees: list[str] | None = None
    topics_discussed: str | None = None
    materials_shared: list[str] | None = None
    samples_distributed: list[str] | None = None
    sentiment: str | None = None
    outcomes: str | None = None
    follow_up_actions: str | None = None


class InteractionRead(InteractionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ai_summary: str = ""
    ai_suggested_followups: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


# --------------------------- Follow-up -------------------------
class FollowUpRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    interaction_id: int | None = None
    hcp_id: int | None = None
    hcp_name: str = ""
    description: str
    due_date: str = ""
    status: str = "pending"


# ----------------------------- AI ------------------------------
class SummarizeRequest(BaseModel):
    text: str
    hcp_name: str = ""


class SummarizeResponse(BaseModel):
    """Structured fields extracted by the LLM from free text / a voice note."""

    summary: str = ""
    topics_discussed: str = ""
    sentiment: str = "Neutral"
    attendees: list[str] = Field(default_factory=list)
    materials_shared: list[str] = Field(default_factory=list)
    samples_distributed: list[str] = Field(default_factory=list)
    outcomes: str = ""
    suggested_followups: list[str] = Field(default_factory=list)


class SuggestFollowupsRequest(BaseModel):
    hcp_name: str = ""
    topics_discussed: str = ""
    outcomes: str = ""
    sentiment: str = "Neutral"


class SuggestFollowupsResponse(BaseModel):
    suggestions: list[str] = Field(default_factory=list)


# ---------------------------- Chat -----------------------------
class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default"


class ChatEvent(BaseModel):
    tool: str
    result: dict | list | str | None = None


class ChatResponse(BaseModel):
    reply: str
    events: list[ChatEvent] = Field(default_factory=list)
    llm_enabled: bool = True
