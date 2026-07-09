"""Groq LLM factory + JSON extraction helpers used by tools and routers."""
import json
import re

from ..config import settings

# Cache one client per model name so we don't rebuild on every call.
_clients: dict[str, object] = {}


def get_llm(reasoning: bool = False, temperature: float = 0.2):
    """Return a cached ChatGroq client.

    reasoning=True selects the larger llama-3.3-70b model for tasks that need
    stronger reasoning (insights / next-best-action); otherwise the faster
    llama-3.1-8b model is used.

    `max_retries` lets the underlying Groq client automatically wait out and retry
    transient 429s (Groq honors the `Retry-After` header with exponential backoff),
    so short bursts on the free tier self-heal instead of surfacing an error.
    `max_tokens` caps the completion so responses don't needlessly eat into the
    per-minute token budget.
    """
    if not settings.llm_enabled:
        raise RuntimeError(
            "GROQ_API_KEY is not configured. Add it to backend/.env to enable AI features."
        )

    from langchain_groq import ChatGroq  # imported lazily so the app boots without the key

    model = settings.groq_model_reasoning if reasoning else settings.groq_model
    key = f"{model}:{temperature}"
    if key not in _clients:
        _clients[key] = ChatGroq(
            model=model,
            temperature=temperature,
            api_key=settings.groq_api_key,
            max_retries=settings.groq_max_retries,
            max_tokens=1536 if reasoning else 1024,
        )
    return _clients[key]


def extract_json(text: str) -> dict:
    """Best-effort parse of a JSON object out of an LLM response."""
    if not text:
        return {}
    text = text.strip()
    # Strip ```json fences if present.
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    else:
        brace = re.search(r"\{.*\}", text, re.DOTALL)
        if brace:
            text = brace.group(0)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


def llm_json(system_prompt: str, user_prompt: str, reasoning: bool = False) -> dict:
    """Run a single prompt and return a parsed JSON dict."""
    llm = get_llm(reasoning=reasoning)
    from langchain_core.messages import HumanMessage, SystemMessage

    resp = llm.invoke(
        [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    )
    return extract_json(resp.content)
