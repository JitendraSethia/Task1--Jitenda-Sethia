# Backend image for the AI-First CRM (FastAPI + LangGraph + Groq).
# Python 3.12 (stable wheels for every dependency, incl. the Postgres driver).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install Python deps first (better layer caching). psycopg[binary] is added here
# so the container talks to PostgreSQL out of the box, while requirements.txt stays
# SQLite-only for zero-config local dev.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt "psycopg[binary]>=3.2"

COPY app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
