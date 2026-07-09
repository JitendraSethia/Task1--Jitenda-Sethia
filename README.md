# AI-First CRM — HCP Module · Log Interaction Screen

An AI-first Customer Relationship Management (CRM) module for pharmaceutical **field
sales representatives**. It implements the **"Log HCP Interaction"** screen, letting a
rep record an interaction with a Healthcare Professional (HCP) in **two ways**:

1. **Structured form** — the classic fields (HCP, type, date, attendees, topics,
   materials, samples, sentiment, outcomes, follow-ups) with AI assists.
2. **Conversational chat** — a **LangGraph agent** that understands natural language
   ("*Met Dr. Smith, discussed Product X efficacy, positive sentiment, left a
   brochure and 2 samples*") and logs, edits, recalls, schedules, and advises — all
   by calling tools.

A **Recent Interactions & Follow-ups** panel sits under the form and updates live
whenever anything is logged, edited or scheduled (via form *or* chat) — so the
results of the `search`, `schedule` and `insights` tools are visible in the UI, not
only in the chat transcript.

> **Stack:** React + Redux (frontend) · FastAPI (backend) · **LangGraph** agent ·
> **Groq** LLMs · SQLAlchemy (SQLite by default, PostgreSQL supported) · Google
> **Inter** font.

> ⚠️ **Model note:** the assignment specified `gemma2-9b-it`, but Groq has since
> **decommissioned** that model (its API now returns `model_decommissioned`). This
> project therefore uses currently-supported Groq models — `llama-3.1-8b-instant`
> for fast form extraction and **`llama-3.3-70b-versatile`** (explicitly sanctioned
> by the assignment) for the agent's tool-calling and insights. Both are set in
> `backend/.env` and are one-line configurable.

---

## 1. What the task is (my understanding)

A field rep's most repetitive job is *logging what happened* after every visit/call.
A traditional form is slow and rigid. This module keeps the structured form (for
compliance and clean data) **but** adds an AI layer:

- The **LLM** turns messy free-text / voice notes into clean structured fields
  (summarization + entity extraction: topics, sentiment, attendees, materials,
  samples, outcomes, follow-ups).
- A **LangGraph agent** acts as the rep's assistant. It decides *which tool* to run
  based on what the rep says, chains tools when needed, and remembers the
  conversation. This is the "AI-first" part: the primary interface can be a
  conversation, and the form simply mirrors what the agent did.

---

## 2. The LangGraph Agent

### Role
The agent is the conversational brain of the Log Interaction screen. It runs a
**ReAct loop** (reason → act → observe) built with `create_react_agent`. Given a
rep's message it:

1. Interprets intent (log new? edit existing? recall history? schedule? advise?).
2. Picks and calls the right **tool(s)**, chaining them when a task needs more than one.
3. Observes each tool's result and replies conversationally.
4. Keeps **per-conversation memory** via a LangGraph checkpointer (`thread_id`).

The API surfaces the tools the agent invoked, so the React form on the left updates
live whenever the agent logs or edits an interaction.

### The 5 Tools (`backend/app/agent/tools.py`)

| # | Tool | Purpose |
|---|------|---------|
| 1 | **`log_interaction`** *(required)* | Captures a **new** interaction from free text. Uses the LLM to **summarize** and **extract entities** (topics, sentiment, attendees, materials shared, samples distributed, outcomes, suggested follow-ups), then persists it. |
| 2 | **`edit_interaction`** *(required)* | **Modifies** an already-logged interaction. Targets a specific id, or the most recent interaction for a named HCP. Only the fields provided are changed. |
| 3 | **`search_interactions`** | Retrieves interaction **history** for an HCP (or the most recent overall) so the rep/agent can recall past context. |
| 4 | **`schedule_follow_up`** | Creates a **follow-up task** (description, HCP, due date) linked to an interaction. |
| 5 | **`get_hcp_insights`** | Analyzes the full history and returns an AI **relationship summary, sentiment trend, talking points, and the single Next Best Action** (uses `llama-3.3-70b-versatile` for stronger reasoning). |

---

## 3. Architecture

```
                 ┌────────────────────────────────────────────┐
                 │   React + Redux Toolkit (Vite, Inter font)  │
                 │  ┌───────────────┐   ┌───────────────────┐  │
                 │  │ Structured    │   │  AI Assistant      │ │
                 │  │ Log form      │   │  (chat panel)      │ │
                 │  └──────┬────────┘   └─────────┬─────────┘  │
                 └─────────┼──────────────────────┼────────────┘
                     REST /api/*              POST /api/chat
                           │                      │
                 ┌─────────▼──────────────────────▼────────────┐
                 │                FastAPI                       │
                 │  routers/interactions.py   routers/chat.py   │
                 │        │                        │            │
                 │   ai_service.py           agent/graph.py     │
                 │   (summarize,         (LangGraph ReAct agent)│
                 │    suggest, insights)      agent/tools.py    │
                 │        │                        │            │
                 │        └──────── crud.py ───────┘            │
                 │              SQLAlchemy models               │
                 └───────────────────┬──────────────────────────┘
                          SQLite (default) / PostgreSQL
                                     │
                            Groq API (LLMs)
```

Both entry points (form REST calls and the chat agent's tools) go through the **same
`crud.py`**, so data logged via chat and via the form is identical and consistent.

---

## 4. Getting Started

### Prerequisites
- **Python 3.11+** (developed on 3.14)
- **Node.js 18+**
- A **free Groq API key** → https://console.groq.com/keys

### 4.1 Backend

```bash
cd backend

# create + activate a virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt

# configure your key
cp .env.example .env          # Windows: copy .env.example .env
#   then edit .env and set GROQ_API_KEY=...

# run
uvicorn app.main:app --reload --port 8000
```

Backend runs at **http://localhost:8000** · interactive API docs at
**http://localhost:8000/docs**.

### 4.2 Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at **http://localhost:5173** and proxies `/api` to the backend
automatically (see `vite.config.js`).

> **Without a Groq key** the app still boots and the structured form works fully; AI
> features (chat, summarize, suggestions, insights) return a friendly "configure your
> key" message instead of failing.

### 4.3 Using PostgreSQL (assignment preference)

SQLite is the zero-config default for local dev. Two ways to run on Postgres:

**A) One command with Docker (recommended)** — spins up Postgres **and** the backend:

```bash
# optional: put your Groq key in a repo-root .env  ->  GROQ_API_KEY=gsk_...
docker compose up --build
```

This starts PostgreSQL 16 and the FastAPI backend (wired to it via
`DATABASE_URL`) on **http://localhost:8000**. Then run the frontend locally
(`cd frontend && npm install && npm run dev`) — Vite proxies `/api` to the
backend. The `/api/health` endpoint reports the active database so you can
confirm Postgres is in use.

**B) Manual** — point the local backend at any Postgres:

```bash
pip install "psycopg[binary]>=3.2"
```

Set in `backend/.env`:

```
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/hcp_crm
```

Tables are created (and sample data seeded) automatically on startup.

---

## 5. API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET  | `/api/health` | Health + which model / DB is active |
| GET  | `/api/hcps?q=` | List / search seeded HCPs |
| POST | `/api/interactions` | Create an interaction (structured form) |
| GET  | `/api/interactions?hcp_name=` | List interactions |
| GET  | `/api/interactions/{id}` | Get one |
| PUT  | `/api/interactions/{id}` | Update one |
| POST | `/api/ai/summarize` | LLM: free text/voice note → structured fields |
| POST | `/api/ai/suggest-followups` | LLM: suggested follow-up actions |
| GET  | `/api/follow-ups?hcp_name=` | List scheduled follow-ups |
| POST | `/api/chat` | **Drive the LangGraph agent** |

---

## 6. Project Structure

```
.
├── docker-compose.yml          # Postgres + backend (one-command Postgres setup)
├── backend/
│   ├── Dockerfile              # backend image (Python 3.12 + psycopg)
│   ├── app/
│   │   ├── main.py              # FastAPI app, CORS, startup (create tables + seed)
│   │   ├── config.py           # env settings (Groq key, DB URL, models)
│   │   ├── database.py         # SQLAlchemy engine/session (SQLite or Postgres)
│   │   ├── models.py           # HCP, Interaction, FollowUp tables
│   │   ├── schemas.py          # Pydantic request/response models
│   │   ├── crud.py             # shared DB access (form + agent)
│   │   ├── ai_service.py       # LLM summarize / suggest / insights
│   │   ├── seed.py             # sample HCPs + sample interactions/follow-ups
│   │   ├── agent/
│   │   │   ├── llm.py          # Groq (ChatGroq) client factory + JSON parsing
│   │   │   ├── tools.py        # the 5 LangGraph tools
│   │   │   └── graph.py        # LangGraph ReAct agent + run_agent()
│   │   └── routers/
│   │       ├── interactions.py # REST endpoints for the form + AI helpers
│   │       └── chat.py         # chat endpoint → agent
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   ├── api/client.js       # axios calls to /api
│   │   ├── store/
│   │   │   ├── store.js
│   │   │   └── slices/
│   │   │       ├── interactionSlice.js   # form state + thunks
│   │   │       ├── chatSlice.js          # chat state + agent calls
│   │   │       └── activitySlice.js      # recent interactions + follow-ups
│   │   ├── components/
│   │   │   ├── LogInteractionForm.jsx
│   │   │   ├── ChatAssistant.jsx
│   │   │   ├── RecentActivity.jsx        # live interactions & follow-ups panel
│   │   │   └── TagInput.jsx
│   │   └── styles/index.css
│   ├── index.html              # loads Google Inter font
│   ├── package.json
│   └── vite.config.js
└── README.md
```

---

## 7. Demo script (for the video — exercises all 5 tools)

In the **AI Assistant** chat panel:

1. **log_interaction** —
   *"Met Dr. Emily Smith today, discussed Product X efficacy, she was positive, left
   a brochure and 2 samples of OncoBoost."*
   → agent extracts fields, logs it, and the **form on the left fills in**.
2. **edit_interaction** —
   *"Actually change the sentiment for Dr. Emily Smith to neutral and add follow-up:
   send Phase III data."*
3. **search_interactions** —
   *"Show my recent interactions with Dr. Emily Smith."*
4. **schedule_follow_up** —
   *"Schedule a follow-up to send the OncoBoost Phase III PDF next Tuesday."*
5. **get_hcp_insights** —
   *"What's the next best action for Dr. Emily Smith?"*

Also demo the **form path**: the 🎙 *Summarize from Voice Note (Requires Consent)*
button (LLM summarization + entity extraction) and the ✨ *AI Suggested Follow-ups*
generator.

---

## 8. Notes

- **Groq models:** `gemma2-9b-it` (the model named in the assignment) has been
  decommissioned by Groq, so this project uses supported models instead:
  `llama-3.1-8b-instant` for fast form summarize/extraction and
  `llama-3.3-70b-versatile` for the LangGraph agent's tool-calling and the heavier
  "insights / next best action" reasoning. Configurable in `.env`.
- **State management:** Redux Toolkit — `interactionSlice` (form + async thunks) and
  `chatSlice` (conversation; mirrors agent-logged records back into the form).
- **Consent:** the voice-note summarizer requires an explicit consent checkbox before
  any note is processed — appropriate for a life-science / HCP context.
- **Rate limits (Groq free tier):** the LLM client auto-retries transient `429`s with
  backoff (honoring `Retry-After`, `GROQ_MAX_RETRIES=5`), the insights tool only sends
  the most recent interactions to keep prompts small, and completions are token-capped.
  If a 429 still gets through, the chat replies with a clear "wait a few seconds" message
  (not "rephrase"). For heavy testing you can also lower load by pointing
  `GROQ_MODEL_REASONING` at `llama-3.1-8b-instant`, or enable Groq billing for higher limits.
