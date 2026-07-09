"""Application configuration loaded from environment / .env file."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/ (parent of the app package) — used to locate .env regardless of the
# directory uvicorn is launched from.
_BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    # Groq / LLM
    # NOTE: the assignment named `gemma2-9b-it`, but Groq has since decommissioned
    # that model. We use currently-supported Groq models instead (the assignment
    # explicitly sanctions `llama-3.3-70b-versatile` as an alternative).
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-8b-instant"          # fast: form summarize/extract
    groq_model_reasoning: str = "llama-3.3-70b-versatile"  # agent + insights
    # Auto-retry (with backoff, honoring Retry-After) on transient 429s so short
    # bursts on Groq's free tier self-heal instead of erroring out.
    groq_max_retries: int = 5

    # Database
    database_url: str = "sqlite:///./hcp_crm.db"

    # CORS
    frontend_origin: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=_BACKEND_DIR / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    @property
    def llm_enabled(self) -> bool:
        """True when a Groq key is configured so AI features are live."""
        return bool(self.groq_api_key and self.groq_api_key != "your_groq_api_key_here")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
