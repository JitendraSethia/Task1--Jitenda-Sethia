"""FastAPI application entry point for the AI-First CRM — HCP Log Interaction module."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import Base, engine
from .routers import chat, interactions
from .seed import seed_hcps


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Create tables and seed sample HCPs on startup.
    Base.metadata.create_all(bind=engine)
    seed_hcps()
    yield


app = FastAPI(
    title="AI-First CRM — HCP Interaction Module",
    description="Log Interaction screen backend: FastAPI + LangGraph + Groq.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(interactions.router)
app.include_router(chat.router)


@app.get("/api/health", tags=["health"])
def health():
    return {
        "status": "ok",
        "llm_enabled": settings.llm_enabled,
        "model": settings.groq_model,
        "database": settings.database_url.split("://", 1)[0],
    }
