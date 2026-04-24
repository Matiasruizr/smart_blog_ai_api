# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Activate venv (Python 3.13)
source .venv/bin/activate

# Run dev server
uvicorn app.main:app --reload --port 8000

# Run tests
pytest
pytest --cov=app --cov-report=term-missing
pytest tests/test_foo.py::test_bar   # single test

# Lint and format
black app/
ruff check app/
```

Interactive docs: `http://localhost:8000/docs`

## Architecture

FastAPI backend for Smart Blog AI. Connects a Next.js frontend to MongoDB Atlas, Claude (Anthropic), and LinkedIn.

**Tech stack:** FastAPI, Python 3.13, MongoDB Atlas via `motor` (async) + `Beanie` ODM, Anthropic SDK (`claude-sonnet-4-6`), APScheduler for the 48h cycle, `python-jose` for JWT, `httpx` for outbound HTTP (LinkedIn API, scrapers).

**Current state:** Directory structure is in place but most files are empty stubs. Only `app/main.py` has real code — a bare FastAPI app with a single `GET /health` endpoint. Routers are not yet mounted; the `/api/v1` prefix and all business logic still need implementing.

### Layer responsibilities

| Layer | Path | Role |
|---|---|---|
| Entry point | `app/main.py` | FastAPI app creation, router registration, lifespan (DB init, scheduler start) |
| Config | `app/config.py` | `pydantic-settings` `BaseSettings` — single source of truth for all env vars |
| DB | `app/database.py` | `motor` client + `Beanie` document init |
| Models | `app/models/` | Beanie `Document` subclasses (persisted to MongoDB) |
| Schemas | `app/schemas/` | Pydantic request/response shapes (not DB models — kept separate) |
| Routers | `app/routers/` | HTTP layer only; delegate to services |
| Services | `app/services/` | All business logic; no FastAPI/HTTP imports |
| Core | `app/core/` | `auth.py` JWT, `security.py` password hashing, `dependencies.py` DI |

### Key flows

**48h automation cycle** (`scheduler.py` → `trending_service` → `email_service` → webhook → `ai_service`):
1. Scrapes Hacker News + GitHub trending; Claude ranks/summarizes 3–5 topics
2. Emails owner topic suggestions with proposed briefs
3. Owner approves via web UI or email → `POST /api/v1/webhooks/brief-submitted`
4. Claude generates a full Markdown post → saved as draft `BlogPost` in MongoDB
5. If `auto_publish=true`, publishes and optionally shares to LinkedIn

**Auth model:** JWT for all owner/admin routes. LinkedIn uses OAuth 2.0 Authorization Code; tokens stored encrypted in MongoDB. `GET /posts` and `GET /profile` are intentionally public.

### API prefix

All routes: `/api/v1`. Health check: `GET /health` (currently outside the prefix in `main.py`).

## Environment

All config via `pydantic-settings` `BaseSettings` reading from `.env` (see `.env.example`). Key variables: `MONGODB_URI`, `MONGODB_DB_NAME`, `ANTHROPIC_API_KEY`, `AI_MODEL`, `SECRET_KEY`, `ALLOWED_ORIGINS`, `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET`, `EMAIL_PROVIDER` (`smtp` or `sendgrid`), `SCHEDULER_ENABLED`, `AUTOMATION_INTERVAL_HOURS`.

Tests use `MONGODB_DB_NAME=test_smart_blog_ai`; LinkedIn and email services should be mocked.

## Conventions

- Type hints required on all functions
- All endpoints need Pydantic schemas for request and response (in `schemas/`, not inline)
- Models (`app/models/`) are Beanie `Document`s; schemas (`app/schemas/`) are plain Pydantic — never mix
- Branch naming: `feature/short-description`, `fix/short-description`
- Commits: Conventional Commits — `feat:`, `fix:`, `chore:`, `docs:`
- Run `black` + `ruff` before committing
