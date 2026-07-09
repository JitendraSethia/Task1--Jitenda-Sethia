"""Chat endpoint that drives the LangGraph agent (conversational logging)."""
from fastapi import APIRouter

from .. import schemas
from ..agent.graph import run_agent

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=schemas.ChatResponse)
def chat(payload: schemas.ChatRequest):
    result = run_agent(payload.message, thread_id=payload.thread_id)
    return schemas.ChatResponse(
        reply=result["reply"],
        events=[schemas.ChatEvent(**e) for e in result["events"]],
        llm_enabled=result["llm_enabled"],
    )
