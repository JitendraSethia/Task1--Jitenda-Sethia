"""The five sales-related tools the LangGraph agent can call.

Required tools:
  1. log_interaction     - capture a new interaction (LLM summarization + entity extraction)
  2. edit_interaction    - modify an already-logged interaction
Additional sales tools:
  3. search_interactions - retrieve interaction history for an HCP
  4. schedule_follow_up  - create a follow-up task for the rep
  5. get_hcp_insights    - AI relationship summary + next-best-action recommendation

Each tool opens its own short-lived DB session so it is safe to call from the
agent runtime, and returns a JSON-serializable dict.
"""
from langchain_core.tools import tool

from .. import ai_service, crud
from ..database import SessionLocal


def _to_int(value) -> int | None:
    """Coerce a possibly-stringified number to int (LLMs often emit "1" not 1)."""
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _interaction_to_dict(i) -> dict:
    return {
        "id": i.id,
        "hcp_name": i.hcp_name,
        "interaction_type": i.interaction_type,
        "date": i.date,
        "time": i.time,
        "attendees": i.attendees or [],
        "topics_discussed": i.topics_discussed,
        "materials_shared": i.materials_shared or [],
        "samples_distributed": i.samples_distributed or [],
        "sentiment": i.sentiment,
        "outcomes": i.outcomes,
        "follow_up_actions": i.follow_up_actions,
        "ai_summary": i.ai_summary,
        "ai_suggested_followups": i.ai_suggested_followups or [],
    }


@tool
def log_interaction(note: str, hcp_name: str, date: str = "", time: str = "") -> dict:
    """Log a NEW interaction with a Healthcare Professional (HCP).

    Pass the rep's free-text description of the meeting/call in `note`. The tool
    uses the LLM to summarize the note and extract structured fields (topics,
    sentiment, attendees, materials shared, samples distributed, outcomes and
    suggested follow-ups), persists the interaction, and returns the saved record.

    Args:
        note: Free-text account of what happened during the interaction.
        hcp_name: REQUIRED. The HCP's name (e.g. "Dr. Smith"). Always extract this
            from the rep's message and pass it explicitly.
        date: Interaction date as YYYY-MM-DD. Optional.
        time: Interaction time as HH:MM. Optional.
    """
    db = SessionLocal()
    try:
        extracted = ai_service.summarize_interaction(note, hcp_name)
        payload = {
            "hcp_name": hcp_name or extracted.get("hcp_name", "") or "",
            "date": date,
            "time": time,
            "topics_discussed": extracted["topics_discussed"],
            "sentiment": extracted["sentiment"],
            "attendees": extracted["attendees"],
            "materials_shared": extracted["materials_shared"],
            "samples_distributed": extracted["samples_distributed"],
            "outcomes": extracted["outcomes"],
            "ai_summary": extracted["summary"],
            "ai_suggested_followups": extracted["suggested_followups"],
        }
        interaction = crud.create_interaction(db, payload)
        result = _interaction_to_dict(interaction)
        result["_message"] = f"Logged interaction #{interaction.id} with {interaction.hcp_name or 'HCP'}."
        return result
    finally:
        db.close()


@tool
def edit_interaction(
    interaction_id: int | str | None = None,
    hcp_name: str = "",
    topics_discussed: str | None = None,
    sentiment: str | None = None,
    outcomes: str | None = None,
    follow_up_actions: str | None = None,
    interaction_type: str | None = None,
    date: str | None = None,
    time: str | None = None,
    materials_shared: list[str] | None = None,
    samples_distributed: list[str] | None = None,
    attendees: list[str] | None = None,
) -> dict:
    """Edit / modify an EXISTING logged interaction.

    Provide `interaction_id` to target a specific record. If it is omitted but
    `hcp_name` is given, the most recent interaction for that HCP is edited.
    Only the fields you pass are changed; everything else is left untouched.

    Args:
        interaction_id: ID of the interaction to edit.
        hcp_name: Used to find the latest interaction if no id is given.
        topics_discussed / sentiment / outcomes / follow_up_actions /
        interaction_type / date / time: replacement scalar values.
        materials_shared / samples_distributed / attendees: replacement lists.
    """
    db = SessionLocal()
    try:
        interaction_id = _to_int(interaction_id)
        target = None
        found_by_id = False
        if interaction_id is not None:
            target = crud.get_interaction(db, interaction_id)
            found_by_id = target is not None
        elif hcp_name:
            target = crud.latest_interaction_for_hcp(db, hcp_name)

        if not target:
            return {"error": "No matching interaction found to edit."}

        patch = {
            "topics_discussed": topics_discussed,
            "sentiment": sentiment,
            "outcomes": outcomes,
            "follow_up_actions": follow_up_actions,
            "interaction_type": interaction_type,
            "date": date,
            "time": time,
            "materials_shared": materials_shared,
            "samples_distributed": samples_distributed,
            "attendees": attendees,
        }
        patch = {k: v for k, v in patch.items() if v is not None}

        # Rename the HCP only when the record was located by id. If it was found
        # via `hcp_name`, that name was the (possibly partial) search key, not a
        # new value — patching it would corrupt the stored name.
        if found_by_id and hcp_name:
            hcp = crud.get_or_create_hcp(db, hcp_name)
            patch["hcp_name"] = hcp.name if hcp else hcp_name
            if hcp:
                patch["hcp_id"] = hcp.id

        updated = crud.update_interaction(db, target.id, patch)
        result = _interaction_to_dict(updated)
        result["_message"] = f"Updated interaction #{updated.id}."
        return result
    finally:
        db.close()


@tool
def search_interactions(hcp_name: str = "", limit: int | str = 10) -> dict:
    """Search past interactions, optionally filtered by HCP name.

    Use this to recall the history with an HCP before logging or advising.

    Args:
        hcp_name: Filter to a specific HCP (partial match). Empty = most recent overall.
        limit: Maximum number of records to return.
    """
    db = SessionLocal()
    try:
        rows = crud.list_interactions(db, hcp_name=hcp_name, limit=_to_int(limit) or 10)
        return {
            "count": len(rows),
            "interactions": [_interaction_to_dict(r) for r in rows],
        }
    finally:
        db.close()


@tool
def schedule_follow_up(
    description: str,
    hcp_name: str = "",
    due_date: str = "",
    interaction_id: int | str | None = None,
) -> dict:
    """Schedule a follow-up task/action for a specific HCP.

    Args:
        description: What needs to be done (e.g. "Send OncoBoost Phase III PDF").
        hcp_name: The HCP this follow-up relates to.
        due_date: Target date as YYYY-MM-DD (optional).
        interaction_id: Link the follow-up to a specific interaction (optional).
    """
    db = SessionLocal()
    try:
        follow_up = crud.create_follow_up(
            db,
            {
                "description": description,
                "hcp_name": hcp_name,
                "due_date": due_date,
                "interaction_id": _to_int(interaction_id),
            },
        )
        return {
            "id": follow_up.id,
            "description": follow_up.description,
            "hcp_name": follow_up.hcp_name,
            "due_date": follow_up.due_date,
            "status": follow_up.status,
            "_message": f"Follow-up scheduled for {hcp_name or 'HCP'}.",
        }
    finally:
        db.close()


@tool
def get_hcp_insights(hcp_name: str) -> dict:
    """Get an AI relationship summary and the recommended NEXT BEST ACTION for an HCP.

    Analyzes the full interaction history to report sentiment trend, a relationship
    summary, suggested talking points, and the single most valuable next step.

    Args:
        hcp_name: The HCP to analyze.
    """
    db = SessionLocal()
    try:
        rows = crud.list_interactions(db, hcp_name=hcp_name, limit=50)
        history = [_interaction_to_dict(r) for r in rows]
        insights = ai_service.generate_insights(hcp_name, history)
        insights["history_count"] = len(history)
        return insights
    finally:
        db.close()


ALL_TOOLS = [
    log_interaction,
    edit_interaction,
    search_interactions,
    schedule_follow_up,
    get_hcp_insights,
]
