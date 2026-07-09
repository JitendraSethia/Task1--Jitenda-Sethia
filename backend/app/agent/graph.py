"""LangGraph ReAct agent that orchestrates the HCP interaction tools.

Role of the agent
-----------------
The agent is the conversational "brain" of the Log Interaction screen. A field rep
can talk to it in natural language ("Met Dr. Smith, discussed Product X efficacy,
positive sentiment, left a brochure"). The agent decides which tool(s) to invoke —
logging the interaction, editing a prior one, recalling history, scheduling a
follow-up, or generating next-best-action insights — chains them as needed, and
replies conversationally. LangGraph manages the reason→act→observe loop and (via a
checkpointer) keeps per-conversation memory across turns.
"""
from functools import lru_cache

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from ..config import settings
from .llm import get_llm
from .tools import ALL_TOOLS

SYSTEM_PROMPT = """You are the AI assistant inside an AI-first pharmaceutical CRM, \
embedded in the "Log HCP Interaction" screen. You help field sales representatives \
log and manage their interactions with Healthcare Professionals (HCPs).

You can:
- log_interaction: capture a brand-new interaction from the rep's free-text note.
- edit_interaction: modify an interaction that was already logged.
- search_interactions: recall past interactions for an HCP.
- schedule_follow_up: create a follow-up task.
- get_hcp_insights: summarize the relationship and recommend the next best action.

Guidelines:
- When the rep describes a meeting/call/visit that just happened, call log_interaction.
- When they ask to change/correct/update a logged interaction, call edit_interaction.
- Prefer calling a tool over guessing. After a tool runs, confirm what you did in one
  or two clear sentences, mentioning the interaction id when relevant.
- Never invent clinical facts. Be concise and professional."""


@lru_cache
def get_agent():
    """Build (once) and return the compiled LangGraph agent.

    Uses the larger `llama-3.3-70b-versatile` model for dependable multi-tool
    (function) calling in the ReAct loop.
    """
    llm = get_llm(reasoning=True, temperature=0.1)
    checkpointer = MemorySaver()
    return create_react_agent(
        llm,
        tools=ALL_TOOLS,
        prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
    )


def run_agent(message: str, thread_id: str = "default") -> dict:
    """Invoke the agent for one user turn.

    Returns the assistant's reply plus a list of tool events (name + result) so the
    frontend can react (e.g. refresh the interaction list when one is logged/edited).
    """
    if not settings.llm_enabled:
        return {
            "reply": (
                "AI is not configured yet. Add your GROQ_API_KEY to backend/.env and "
                "restart the server to enable the chat assistant."
            ),
            "events": [],
            "llm_enabled": False,
        }

    agent = get_agent()
    config = {"configurable": {"thread_id": thread_id}}
    try:
        result = agent.invoke(
            {"messages": [HumanMessage(content=message)]}, config=config
        )
    except Exception as exc:  # e.g. a malformed tool call or provider rate limit
        if _is_rate_limit(exc):
            reply = (
                "I'm being rate-limited by the model provider (Groq free tier) right "
                "now. Please wait a few seconds and send that again — no need to "
                "rephrase. Tip: heavy multi-step requests use the most quota."
            )
        else:
            reply = (
                "I hit a problem completing that request. Could you rephrase it? "
                f"(details: {type(exc).__name__})"
            )
        return {"reply": reply, "events": [], "llm_enabled": True}

    all_messages = result["messages"]

    # The checkpointer returns the FULL conversation. Slice to just this turn
    # (everything after the last HumanMessage) so events/reply aren't cumulative.
    start = 0
    for idx in range(len(all_messages) - 1, -1, -1):
        if isinstance(all_messages[idx], HumanMessage):
            start = idx
            break
    messages = all_messages[start:]

    events: list[dict] = []
    reply = ""

    # Map tool_call_id -> tool name for labeling ToolMessages.
    tool_names: dict[str, str] = {}
    for msg in messages:
        if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
            for call in msg.tool_calls:
                tool_names[call["id"]] = call["name"]

    for msg in messages:
        if isinstance(msg, ToolMessage):
            events.append(
                {
                    "tool": tool_names.get(msg.tool_call_id, "tool"),
                    "result": _safe_content(msg.content),
                }
            )

    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.content:
            reply = msg.content if isinstance(msg.content, str) else str(msg.content)
            break

    return {"reply": reply, "events": events, "llm_enabled": True}


def _is_rate_limit(exc: Exception) -> bool:
    """True if the exception is (or wraps) a Groq 429 rate-limit error."""
    if getattr(exc, "status_code", None) == 429:
        return True
    text = f"{type(exc).__name__} {exc}".lower()
    return "ratelimit" in text or "rate limit" in text or "429" in text


def _safe_content(content):
    """ToolMessage.content may be a str (often JSON). Parse to dict/list when possible."""
    import json

    if isinstance(content, (dict, list)):
        return content
    if isinstance(content, str):
        try:
            return json.loads(content)
        except (json.JSONDecodeError, ValueError):
            return content
    return str(content)
