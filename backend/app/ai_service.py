"""LLM-powered helpers: summarization, entity extraction, follow-up suggestions,
and HCP relationship insights. Shared by REST routers and LangGraph tools."""
from .agent.llm import llm_json
from .config import settings

VALID_SENTIMENTS = {"Positive", "Neutral", "Negative"}

# How many recent interactions to feed the insights model (keeps the prompt small).
RECENT_HISTORY_FOR_INSIGHTS = 6


def _norm_sentiment(value: str) -> str:
    value = (value or "").strip().capitalize()
    return value if value in VALID_SENTIMENTS else "Neutral"


def _to_str_list(items) -> list[str]:
    """Coerce an LLM list into a clean list[str].

    The model sometimes returns structured items, e.g.
    {"name": "OncoBoost", "quantity": 2} -> "OncoBoost x2".
    """
    if isinstance(items, (str, dict)):
        items = [items]
    out: list[str] = []
    for it in items or []:
        if isinstance(it, str):
            s = it.strip()
        elif isinstance(it, dict):
            name = it.get("name") or it.get("item") or it.get("material") or it.get("title") or ""
            qty = it.get("quantity") or it.get("qty") or it.get("count") or it.get("dose")
            if name:
                s = f"{name} x{qty}".strip() if qty else str(name).strip()
            elif len(it) == 1:
                # e.g. {"OncoBoost": 2} -> "OncoBoost x2"
                k, v = next(iter(it.items()))
                s = f"{k} x{v}" if isinstance(v, (int, float)) else f"{k}: {v}"
            else:
                s = ", ".join(f"{k} {v}" for k, v in it.items())
        else:
            s = str(it).strip()
        if s:
            out.append(s)
    return out


def summarize_interaction(text: str, hcp_name: str = "") -> dict:
    """Extract structured interaction fields from a free-text note / voice transcript.

    Uses the LLM for summarization + entity extraction. Falls back to a minimal
    passthrough if no Groq key is configured so the UI never hard-fails.
    """
    if not settings.llm_enabled:
        return {
            "hcp_name": hcp_name,
            "summary": text.strip()[:400],
            "topics_discussed": text.strip(),
            "sentiment": "Neutral",
            "attendees": [],
            "materials_shared": [],
            "samples_distributed": [],
            "outcomes": "",
            "suggested_followups": [],
        }

    system = (
        "You are a pharmaceutical field-sales assistant that structures a rep's "
        "notes about a meeting with a Healthcare Professional (HCP). "
        "Return ONLY a JSON object with these keys: "
        "hcp_name (string, the primary Healthcare Professional's name, e.g. 'Dr. Smith'), "
        "summary (string, 1-2 sentence recap), "
        "topics_discussed (string), "
        "sentiment (one of: Positive, Neutral, Negative), "
        "attendees (array of OTHER people present, EXCLUDING the primary HCP named above), "
        "materials_shared (array of plain-string brochure/document names), "
        "samples_distributed (array of plain strings like 'OncoBoost x2', NOT objects), "
        "outcomes (string, key agreements or results), "
        "suggested_followups (array of concise next-step strings). "
        "All array items MUST be plain strings, never nested objects. "
        "Use empty string/array when unknown. Do not invent facts."
    )
    user = f"HCP: {hcp_name or 'unknown'}\n\nRep note / transcript:\n{text}"
    data = llm_json(system, user)

    return {
        "hcp_name": hcp_name or data.get("hcp_name", "") or "",
        "summary": data.get("summary", ""),
        "topics_discussed": data.get("topics_discussed", "") or text.strip(),
        "sentiment": _norm_sentiment(data.get("sentiment", "Neutral")),
        "attendees": _to_str_list(data.get("attendees")),
        "materials_shared": _to_str_list(data.get("materials_shared")),
        "samples_distributed": _to_str_list(data.get("samples_distributed")),
        "outcomes": data.get("outcomes", "") or "",
        "suggested_followups": _to_str_list(data.get("suggested_followups")),
    }


def suggest_followups(
    hcp_name: str = "",
    topics_discussed: str = "",
    outcomes: str = "",
    sentiment: str = "Neutral",
) -> list[str]:
    """Generate 2-4 concrete, sales-relevant follow-up actions."""
    if not settings.llm_enabled:
        return [
            "Schedule a follow-up meeting in 2 weeks",
            "Send additional product literature",
        ]

    system = (
        "You are an expert pharmaceutical sales strategist. Given the context of an "
        "HCP interaction, propose 2-4 specific, actionable follow-up steps a field rep "
        "should take next (e.g. schedule a call, send a specific document, add to an "
        "advisory board, arrange a sample drop). "
        'Return ONLY JSON: {"suggestions": ["...", "..."]}'
    )
    user = (
        f"HCP: {hcp_name or 'unknown'}\n"
        f"Sentiment: {sentiment}\n"
        f"Topics discussed: {topics_discussed}\n"
        f"Outcomes: {outcomes}"
    )
    data = llm_json(system, user)
    return _to_str_list(data.get("suggestions"))[:4]


def generate_insights(hcp_name: str, history: list[dict]) -> dict:
    """Summarize the relationship with an HCP and recommend the next best action."""
    if not settings.llm_enabled:
        return {
            "relationship_summary": f"{len(history)} interaction(s) logged with {hcp_name}.",
            "sentiment_trend": "unknown",
            "next_best_action": "Configure GROQ_API_KEY to enable AI recommendations.",
            "talking_points": [],
        }

    system = (
        "You are a life-science CRM analyst. Given the interaction history with an HCP, "
        "produce a concise briefing for the field rep's next visit. "
        "Return ONLY JSON with keys: relationship_summary (string), "
        "sentiment_trend (string: improving/stable/declining/unknown), "
        "next_best_action (string, the single most valuable next step), "
        "talking_points (array of 2-4 short strings)."
    )
    # Only the most recent interactions matter for a next-visit briefing; capping
    # the history keeps the prompt small so we stay well under the per-minute token
    # limit (history arrives newest-first from list_interactions).
    recent = history[:RECENT_HISTORY_FOR_INSIGHTS]
    lines = []
    for h in recent:
        lines.append(
            f"- {h.get('date','?')} [{h.get('interaction_type','')}] "
            f"sentiment={h.get('sentiment','')}: {h.get('topics_discussed','')} "
            f"| outcomes: {h.get('outcomes','')}"
        )
    user = (
        f"HCP: {hcp_name}\n"
        f"History (showing {len(recent)} most recent of {len(history)} total):\n"
        + "\n".join(lines)
    )
    data = llm_json(system, user, reasoning=True)
    return {
        "relationship_summary": data.get("relationship_summary", ""),
        "sentiment_trend": data.get("sentiment_trend", "unknown"),
        "next_best_action": data.get("next_best_action", ""),
        "talking_points": _to_str_list(data.get("talking_points")),
    }
