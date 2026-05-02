# Smart Blog AI — FastAPI Backend

> RESTful API powering the Smart Blog AI platform. Connects the Next.js frontend, MongoDB Atlas, the AI content automation engine, and LinkedIn sync.

![Python](https://img.shields.io/badge/Python-3.13-1E293B?style=flat-square) ![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat-square) ![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-00684A?style=flat-square) ![Status](https://img.shields.io/badge/Status-v1.0--alpha-7C3AED?style=flat-square)

---

## Table of Contents

1. [Overview](#1-overview)
2. [Architecture](#2-architecture)
3. [Project Structure](#3-project-structure)
4. [Quick Start](#4-quick-start)
5. [Environment Variables](#5-environment-variables)
6. [API Reference](#6-api-reference)
7. [Automation Flow](#7-automation-flow)
8. [Authentication & Security](#8-authentication--security)
9. [Deployment](#9-deployment)
10. [Running Tests](#10-running-tests)
11. [Contributing & Conventions](#11-contributing--conventions)

---

## 1. Overview

The Smart Blog AI backend is a RESTful API built with FastAPI and Python 3.13. It serves as the central nervous system of the platform, connecting the Next.js frontend, MongoDB Atlas, the AI content automation engine, and the LinkedIn sync module.

**What this API does:**

- Manages blog posts — CRUD, publish/unpublish workflow, soft-delete, page/size pagination
- Exposes portfolio and profile data consumed by the Next.js frontend
- LinkedIn OAuth 2.0 flow — connect, sync profile data, share posts
- AI-powered blog post generation via Claude (Anthropic SDK)
- 48h automation cycle — scrape trending topics, generate post briefs, email owner, create posts
- Outbound email notifications (SMTP / SendGrid) — _coming soon_
- Webhook callbacks for the automation engine — _coming soon_

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  FRONTEND  (Next.js / Vercel)               │
│           Portfolio · Blog · Projects · Contact             │
└──────────────────────┬──────────────────────────────────────┘
                       │  REST / JSON
┌──────────────────────▼──────────────────────────────────────┐
│              API LAYER  (FastAPI / Python 3.13)             │
│   /posts  /profile  /linkedin  /automation  /webhooks       │
└──────┬───────────────┬───────────────┬──────────────────────┘
       │               │               │
  ┌────▼────┐  ┌───────▼──────┐  ┌────▼────────────────────┐
  │ MongoDB │  │ LinkedIn API │  │ Automation Engine        │
  │  Atlas  │  │  (OAuth 2.0) │  │ (Claude · APScheduler)  │
  └─────────┘  └──────────────┘  └─────────────────────────┘
```

### Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| API Framework | FastAPI 0.110+ | Async, OpenAPI auto-docs, Pydantic v2 |
| Language | Python 3.13 | Type hints throughout |
| Database | MongoDB Atlas | via `motor` async driver |
| ODM | Beanie 1.26+ | Async ODM on top of motor |
| Auth | JWT (`python-jose`) + OAuth 2.0 | JWT for API, OAuth for LinkedIn |
| Password hashing | `passlib[bcrypt]` | Owner credentials |
| HTTP client | `httpx` | LinkedIn API, image providers |
| Email | SMTP / SendGrid | Configurable via env — _coming soon_ |
| Scheduler | APScheduler | 48h content automation — _coming soon_ |
| AI Layer | Anthropic SDK | Claude `claude-sonnet-4-6` for blog generation |
| Config | `pydantic-settings` | All config from `.env` via `BaseSettings` |
| Deployment | Railway / Docker | |

---

## 3. Project Structure

```
smart-blog-ai-api/
├── app/
│   ├── main.py                  # FastAPI app, lifespan, CORS, router registration
│   ├── config.py                # pydantic-settings BaseSettings + get_settings()
│   ├── database.py              # init_db() — motor client + Beanie init
│   │
│   ├── models/                  # Beanie Document subclasses (MongoDB)
│   │   ├── post.py              # BlogPost — blog_posts collection
│   │   ├── profile.py           # Profile + LinkedInCredentials — profile collection
│   │   └── topic.py             # TrendingTopic — trending_topics collection
│   │
│   ├── schemas/                 # Pydantic request/response shapes (not DB models)
│   │   ├── post.py              # PostBase, PostCreate, PostUpdate, PostResponse
│   │   ├── profile.py           # ProfileBase, ProfileUpdate, ProfileResponse,
│   │   │                        # LinkedInStatusResponse, TokenStatusResponse, ShareResponse
│   │   └── automation.py        # GenerateRequest, TrendingTopicResponse, SchedulerStatusResponse
│   │
│   ├── routers/                 # HTTP layer only — delegate to services
│   │   ├── post.py              # /api/v1/posts  ✅
│   │   ├── profile.py           # /api/v1/profile  ✅
│   │   ├── linkedin.py          # /api/v1/linkedin  ✅
│   │   ├── automation.py        # /api/v1/automation  🔜
│   │   └── webhooks.py          # /api/v1/webhooks  🔜
│   │
│   ├── services/                # All business logic — no FastAPI imports
│   │   ├── post_service.py      # Post CRUD + publish/unpublish/soft-delete  ✅
│   │   ├── profile_service.py   # Profile upsert + LinkedIn credentials  ✅
│   │   ├── linkedin_service.py  # OAuth exchange, profile sync, post sharing  ✅
│   │   ├── ai_service.py        # Claude calls + cover image fetch  🔜
│   │   ├── email_service.py     # SMTP / SendGrid  🔜
│   │   ├── trending_service.py  # HN + GitHub trending scraper  🔜
│   │   └── scheduler.py         # APScheduler 48h job definitions  🔜
│   │
│   └── core/
│       ├── auth.py              # create_access_token / decode_access_token (python-jose)
│       ├── security.py          # hash_password / verify_password (passlib bcrypt)
│       └── dependencies.py      # get_current_user + CurrentUser type alias
│
├── tests/
│   ├── conftest.py              # pytest-asyncio fixture — Beanie + test MongoDB
│   ├── pytest.ini               # asyncio_mode = auto
│   ├── test_config.py
│   ├── test_auth.py
│   ├── models/
│   │   ├── test_post.py
│   │   ├── test_profile.py
│   │   └── test_topic.py
│   ├── schemas/
│   │   ├── test_post_schemas.py
│   │   ├── test_profile_schemas.py
│   │   └── test_automation_schemas.py
│   └── routers/
│       ├── test_posts.py
│       ├── test_profile.py
│       └── test_linkedin.py
│
├── docs/
│   └── superpowers/
│       ├── specs/               # Approved design documents
│       └── plans/               # Implementation plans
│
├── .env.example
├── requirements.txt
└── README.md
```

---

## 4. Quick Start

### Prerequisites

- Python 3.13
- MongoDB Atlas cluster (free tier works for development) or local MongoDB
- Anthropic API key (Claude) — for AI generation
- LinkedIn Developer App — for LinkedIn integration (optional for local dev)

### Local setup

```bash
git clone https://github.com/your-username/smart-blog-ai-api.git
cd smart-blog-ai-api

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env with your credentials

uvicorn app.main:app --reload --port 8000
```

Interactive API docs: `http://localhost:8000/docs` (Swagger UI) · `http://localhost:8000/redoc`

Health check: `GET /health`

---

## 5. Environment Variables

All configuration is loaded from `.env` via Pydantic `BaseSettings`. Never commit `.env` to version control.

### Core

| Variable | Description | Default | Required |
|---|---|---|---|
| `APP_ENV` | `development` / `production` | `development` | No |
| `SECRET_KEY` | JWT signing secret — minimum 64 chars | — | **Yes** |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins | `http://localhost:3000` | No |
| `API_V1_PREFIX` | API prefix | `/api/v1` | No |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT token lifetime | `1440` (24h) | No |
| `FRONTEND_URL` | Frontend URL used for OAuth redirects | `http://localhost:3000` | No |
| `BLOG_URL` | Public blog URL used when sharing posts to LinkedIn | `http://localhost:3000` | No |

### Database

| Variable | Description | Required |
|---|---|---|
| `MONGODB_URI` | Full MongoDB connection string | **Yes** |
| `MONGODB_DB_NAME` | Database name (e.g. `smart_blog_ai`) | **Yes** |

### AI (Anthropic)

| Variable | Description | Default | Required |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | Anthropic Claude API key | — | **Yes** (for generation) |
| `AI_MODEL` | Claude model ID | `claude-sonnet-4-6` | No |
| `AI_MAX_TOKENS` | Max tokens per generation | `4096` | No |

### Image providers (for AI-generated cover images)

| Variable | Description | Default | Required |
|---|---|---|---|
| `UNSPLASH_ACCESS_KEY` | Unsplash API key (free tier: 50 req/hr) | `""` | No |
| `PEXELS_API_KEY` | Pexels API key (free tier: 200 req/hr) | `""` | No |

> The service tries Unsplash first, falls back to Pexels. Posts are created without a cover image if both keys are missing.

### LinkedIn

| Variable | Description | Default | Required |
|---|---|---|---|
| `LINKEDIN_CLIENT_ID` | LinkedIn app Client ID | `""` | No |
| `LINKEDIN_CLIENT_SECRET` | LinkedIn app Client Secret | `""` | No |
| `LINKEDIN_REDIRECT_URI` | OAuth callback URL | `http://localhost:8000/api/v1/linkedin/callback` | No |
| `LINKEDIN_SCOPE` | OAuth scopes | `r_liteprofile w_member_social` | No |

### Email _(coming soon)_

| Variable | Description | Required |
|---|---|---|
| `EMAIL_PROVIDER` | `smtp` or `sendgrid` | When email is enabled |
| `SMTP_HOST` | SMTP server host | If smtp |
| `SMTP_PORT` | SMTP port (587 for TLS) | If smtp |
| `SMTP_USER` | SMTP username | If smtp |
| `SMTP_PASSWORD` | SMTP password | If smtp |
| `SENDGRID_API_KEY` | SendGrid API key | If sendgrid |
| `EMAIL_FROM` | Sender address | When email is enabled |
| `EMAIL_TO_OWNER` | Owner's email for automation notifications | When email is enabled |

### Automation Scheduler _(coming soon)_

| Variable | Description | Default |
|---|---|---|
| `SCHEDULER_ENABLED` | Enable the background scheduler | `true` |
| `AUTOMATION_INTERVAL_HOURS` | Hours between automation runs | `48` |
| `TRENDING_SOURCES` | Comma-separated: `hackernews,github` | `hackernews,github` |

---

## 6. API Reference

All routes are prefixed with `/api/v1`. Protected routes require `Authorization: Bearer <token>`.

### Authentication _(login endpoint coming soon)_

JWT verification is implemented. The login endpoint will be added with the auth router.

| Method | Endpoint | Description | Auth | Status |
|---|---|---|---|---|
| `POST` | `/auth/login` | Obtain a JWT access token | No | 🔜 |

---

### Blog Posts ✅

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `GET` | `/posts` | List published posts | No |
| `GET` | `/posts/drafts` | List draft posts | Yes |
| `GET` | `/posts/{slug}` | Get a published post by slug | No |
| `POST` | `/posts` | Create a new draft post | Yes |
| `PUT` | `/posts/{id}` | Update a post | Yes |
| `PATCH` | `/posts/{id}/publish` | Publish a draft | Yes |
| `PATCH` | `/posts/{id}/unpublish` | Revert to draft | Yes |
| `DELETE` | `/posts/{id}` | Soft-delete a post | Yes |

**Pagination** (`GET /posts`, `GET /posts/drafts`): `?page=1&size=10`

**Post response schema:**

```json
{
  "id": "string",
  "title": "string",
  "slug": "string",
  "content": "string",
  "excerpt": "string",
  "tags": ["string"],
  "status": "draft | published",
  "ai_model": "string",
  "cover_image_url": "string | null",
  "meta_title": "string | null",
  "meta_description": "string | null",
  "topic_id": "string | null",
  "linkedin_post_url": "string | null",
  "published_at": "ISO 8601 | null",
  "created_at": "ISO 8601",
  "updated_at": "ISO 8601"
}
```

---

### Profile ✅

Singleton — one profile per deployment. `PUT /profile` uses upsert semantics.

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `GET` | `/profile` | Get public profile | No |
| `PUT` | `/profile` | Create or update profile | Yes |
| `GET` | `/profile/linkedin-status` | LinkedIn connection status | Yes |

---

### LinkedIn ✅

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `GET` | `/linkedin/auth` | Initiate OAuth 2.0 flow | Yes |
| `GET` | `/linkedin/callback` | OAuth callback (redirect from LinkedIn) | No |
| `POST` | `/linkedin/sync` | Sync name + headline from LinkedIn | Yes |
| `POST` | `/linkedin/share/{post_id}` | Share a published post to LinkedIn | Yes |
| `GET` | `/linkedin/token-status` | Check token validity and expiry | Yes |

---

### Automation 🔜

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `GET` | `/automation/trending` | List pending trending topic suggestions | Yes |
| `POST` | `/automation/generate` | Generate a blog post from a brief via Claude | Yes |
| `GET` | `/automation/status` | Scheduler status and next run time | Yes |
| `POST` | `/automation/run-now` | Force-trigger the automation cycle | Yes |

**Generate request body:**

```json
{
  "subject": "Why MCP is changing AI integrations",
  "brief": "Cover the protocol, real use cases, and adoption curve.",
  "tags": ["AI", "MCP", "integrations"],
  "auto_publish": false
}
```

---

### Webhooks 🔜

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `POST` | `/webhooks/brief-submitted` | Owner approved a brief — triggers post generation | Yes |
| `POST` | `/webhooks/post-published` | Post published — triggers notification email | Yes |

---

## 7. Automation Flow

The 48-hour content cycle _(scheduler and email coming soon — `POST /automation/generate` is available now for manual generation)_:

```
┌─────────────────────────────────────────────────────────────┐
│  Every 48 hours (APScheduler)                🔜             │
│                                                             │
│  1. trending_service.py                                     │
│     → scrapes Hacker News API + GitHub Trending             │
│     → sends list to Claude for ranking & summarization      │
│     → saves TrendingTopic documents in MongoDB              │
│                                                             │
│  2. email_service.py                                        │
│     → sends owner email with 3-5 topic suggestions         │
│       + proposed brief for each                             │
│                                                             │
│  3. Owner approves one brief (web UI or email reply)        │
│     → POST /api/v1/webhooks/brief-submitted                 │
│                                                             │
│  4. ai_service.py                            🔜             │
│     → calls Claude with subject + brief                     │
│     → receives JSON: title, excerpt, content, image term    │
│     → fetches cover image (Unsplash → Pexels fallback)      │
│     → saves draft BlogPost in MongoDB                       │
│                                                             │
│  5. Optional: auto_publish = true                           │
│     → publishes post + shares to LinkedIn                   │
└─────────────────────────────────────────────────────────────┘
```

**Manual generation** (available now):

```bash
curl -X POST http://localhost:8000/api/v1/automation/generate \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"subject": "...", "brief": "...", "tags": [], "auto_publish": false}'
```

---

## 8. Authentication & Security

- All owner/admin endpoints require a **JWT Bearer token** in the `Authorization` header.
- JWT signing uses `python-jose` HS256 with `SECRET_KEY`. Default expiry: 24h (`ACCESS_TOKEN_EXPIRE_MINUTES`).
- Password hashing uses `passlib[bcrypt]`.
- LinkedIn integration uses **OAuth 2.0 Authorization Code** — tokens stored in the `Profile` document (encrypted at the application level in production).
- Public endpoints (`GET /posts`, `GET /profile`) are intentionally unauthenticated for SEO and frontend use.

```
Authorization: Bearer <your-token>
```

---

## 9. Deployment

### Railway (recommended)

1. Connect your GitHub repo to a new Railway project.
2. Add all required environment variables via the Railway dashboard (Variables tab).
3. Railway auto-detects the Dockerfile and builds on push to `main`.
4. Set a custom domain pointing to your Railway service URL.
5. Health check: `GET /health`

### Docker

```bash
docker build -t smart-blog-api .
docker run -p 8000:8000 --env-file .env smart-blog-api
```

### Production checklist

- `APP_ENV=production`
- `SECRET_KEY` — strong random string, minimum 64 chars
- `ALLOWED_ORIGINS` — restricted to your actual frontend domain
- MongoDB Atlas IP allowlist configured for your server
- LinkedIn OAuth tokens rotate every 60 days — monitor via `GET /api/v1/linkedin/token-status`

---

## 10. Running Tests

Requires a local MongoDB instance on `mongodb://localhost:27017`. Tests use the `test_smart_blog_ai` database, which is dropped after each test run.

```bash
source .venv/bin/activate

# All tests
pytest

# With coverage
pytest --cov=app --cov-report=term-missing

# Single test file
pytest tests/routers/test_posts.py -v

# Single test
pytest tests/models/test_post.py::test_blogpost_defaults -v
```

---

## 11. Contributing & Conventions

- **Branch naming:** `feature/short-description`, `fix/short-description`
- **Commits:** [Conventional Commits](https://www.conventionalcommits.org/) — `feat:`, `fix:`, `chore:`, `docs:`
- All endpoints need Pydantic schemas for both request and response (in `schemas/`, never inline)
- Models (`app/models/`) are Beanie `Document`s; schemas (`app/schemas/`) are plain Pydantic — never mix
- Type hints required on all functions
- Run `black` + `ruff` before committing

```bash
black app/
ruff check app/
```

---

*Smart Blog AI · FastAPI Backend · Python 3.13 · Built with FastAPI, MongoDB Atlas & Claude*
