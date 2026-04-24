# Smart Blog AI — FastAPI Backend

> RESTful API powering the Smart Blog AI platform. Connects the Next.js frontend, MongoDB Atlas, the AI content automation engine, and LinkedIn sync.

![Python](https://img.shields.io/badge/Python-3.11+-1E293B?style=flat-square) ![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat-square) ![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-00684A?style=flat-square) ![Status](https://img.shields.io/badge/Status-v1.0--alpha-7C3AED?style=flat-square)

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

The Smart Blog AI backend is a RESTful API built with FastAPI and Python. It serves as the central nervous system of the platform, connecting the Next.js frontend, the MongoDB Atlas database, the AI content automation engine, and the LinkedIn sync module.

**What this API does:**

- Manages blog posts — CRUD, publish workflow, draft/published states
- Exposes portfolio and profile data consumed by the Next.js frontend
- Receives webhook callbacks from the automation engine to trigger post creation
- Sends outbound emails (post published notifications, topic suggestion prompts)
- Syncs professional data bidirectionally with the LinkedIn API
- Exposes a trending topics endpoint used by the 48-hour automation scheduler

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  FRONTEND  (Next.js / Vercel)               │
│           Portfolio · Blog · Projects · Contact             │
└──────────────────────┬──────────────────────────────────────┘
                       │  REST / JSON
┌──────────────────────▼──────────────────────────────────────┐
│              API LAYER  (FastAPI / Python)                  │
│   /posts  /profile  /linkedin  /automation  /webhooks       │
└──────┬───────────────┬───────────────┬──────────────────────┘
       │               │               │
  ┌────▼────┐  ┌───────▼──────┐  ┌────▼────────────────────┐
  │ MongoDB │  │ LinkedIn API │  │ Automation Engine        │
  │  Atlas  │  │  (OAuth 2.0) │  │ (APScheduler / SMTP)    │
  └─────────┘  └──────────────┘  └─────────────────────────┘
```

### Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| API Framework | FastAPI 0.110+ | Async, OpenAPI auto-docs, Pydantic v2 |
| Language | Python 3.11+ | Type hints throughout |
| Database | MongoDB Atlas | via motor (async driver) |
| ODM | Beanie | Async ODM on top of motor |
| Auth | JWT + OAuth 2.0 | JWT for API, OAuth for LinkedIn |
| Email | SMTP / SendGrid | Configurable via env |
| Scheduler | APScheduler | 48h content automation jobs |
| AI Layer | Anthropic SDK | Claude for blog generation |
| Deployment | Railway / Docker | Docker Compose for local dev |

---

## 3. Project Structure

```
smart-blog-ai-api/
├── app/
│   ├── main.py                  # FastAPI app entry point
│   ├── config.py                # Settings from env (Pydantic BaseSettings)
│   ├── database.py              # MongoDB Atlas connection (motor + Beanie)
│   │
│   ├── models/                  # Beanie document models
│   │   ├── post.py              # BlogPost document
│   │   ├── profile.py           # Profile document
│   │   └── topic.py             # TrendingTopic document
│   │
│   ├── routers/                 # FastAPI routers
│   │   ├── posts.py             # /api/v1/posts
│   │   ├── profile.py           # /api/v1/profile
│   │   ├── linkedin.py          # /api/v1/linkedin
│   │   ├── automation.py        # /api/v1/automation
│   │   └── webhooks.py          # /api/v1/webhooks
│   │
│   ├── services/                # Business logic
│   │   ├── ai_service.py        # Claude API calls
│   │   ├── email_service.py     # SMTP / SendGrid
│   │   ├── linkedin_service.py  # LinkedIn OAuth + sync
│   │   ├── trending_service.py  # HN + GitHub trending scraper
│   │   └── scheduler.py        # APScheduler job definitions
│   │
│   ├── schemas/                 # Pydantic request/response schemas
│   │   ├── post.py
│   │   ├── profile.py
│   │   └── automation.py
│   │
│   └── core/
│       ├── auth.py              # JWT creation & verification
│       ├── security.py          # Password hashing, token utils
│       └── dependencies.py      # FastAPI dependency injection
│
├── tests/
│   ├── test_posts.py
│   ├── test_automation.py
│   └── test_linkedin.py
│
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## 4. Quick Start

### Prerequisites

- Python 3.11+
- MongoDB Atlas cluster (free tier works for development)
- Anthropic API key (Claude)
- LinkedIn Developer App with OAuth 2.0 credentials
- SMTP credentials or SendGrid API key

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

Interactive API docs will be at `http://localhost:8000/docs` (Swagger UI) and `http://localhost:8000/redoc`.

### Docker Compose (recommended)

```bash
docker-compose up --build
```

The MongoDB connection points to Atlas (not a local container) — set your Atlas URI in `.env` first.

---

## 5. Environment Variables

All configuration is loaded from `.env` via Pydantic `BaseSettings`. Never commit `.env` to version control.

### Core

| Variable | Description | Required |
|---|---|---|
| `APP_ENV` | Environment: `development` / `production` | Yes |
| `SECRET_KEY` | Secret for JWT signing. Use a long random string. | Yes |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins (your Next.js URL) | Yes |
| `API_V1_PREFIX` | API prefix, default: `/api/v1` | No |

### Database

| Variable | Description | Required |
|---|---|---|
| `MONGODB_URI` | Full MongoDB Atlas connection string | Yes |
| `MONGODB_DB_NAME` | Database name (e.g. `smart_blog_ai`) | Yes |

### AI (Anthropic)

| Variable | Description | Required |
|---|---|---|
| `ANTHROPIC_API_KEY` | Your Anthropic Claude API key | Yes |
| `AI_MODEL` | Model to use, default: `claude-opus-4-5` | No |
| `AI_MAX_TOKENS` | Max tokens per generation, default: `4096` | No |

### Email

| Variable | Description | Required |
|---|---|---|
| `EMAIL_PROVIDER` | `smtp` or `sendgrid` | Yes |
| `SMTP_HOST` | SMTP server host | If smtp |
| `SMTP_PORT` | SMTP port (587 for TLS) | If smtp |
| `SMTP_USER` | SMTP username | If smtp |
| `SMTP_PASSWORD` | SMTP password | If smtp |
| `SENDGRID_API_KEY` | SendGrid API key | If sendgrid |
| `EMAIL_FROM` | Sender address for all outbound emails | Yes |
| `EMAIL_TO_OWNER` | Your personal email to receive automation emails | Yes |

### LinkedIn

| Variable | Description | Required |
|---|---|---|
| `LINKEDIN_CLIENT_ID` | LinkedIn app Client ID | Yes |
| `LINKEDIN_CLIENT_SECRET` | LinkedIn app Client Secret | Yes |
| `LINKEDIN_REDIRECT_URI` | OAuth callback URL | Yes |
| `LINKEDIN_SCOPE` | OAuth scopes, e.g.: `r_liteprofile w_member_social` | Yes |

### Automation Scheduler

| Variable | Description | Required |
|---|---|---|
| `SCHEDULER_ENABLED` | Enable the background scheduler (`true`/`false`) | No |
| `AUTOMATION_INTERVAL_HOURS` | Hours between automation runs, default: `48` | No |
| `TRENDING_SOURCES` | Comma-separated: `hackernews,github,rss` | No |

---

## 6. API Reference

All routes are prefixed with `/api/v1`. Protected routes require `Authorization: Bearer <token>`.

### Authentication

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `POST` | `/auth/login` | Obtain a JWT access token | No |
| `POST` | `/auth/refresh` | Refresh an expired JWT | No |

**Login request body:**

```json
{
  "username": "your-username",
  "password": "your-password"
}
```

---

### Blog Posts

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `GET` | `/posts` | List all published posts (paginated) | No |
| `GET` | `/posts/{slug}` | Get a single post by slug | No |
| `POST` | `/posts` | Create a new blog post (draft) | Yes |
| `PUT` | `/posts/{id}` | Update a post by ID | Yes |
| `PATCH` | `/posts/{id}/publish` | Publish a draft post | Yes |
| `PATCH` | `/posts/{id}/unpublish` | Revert a post to draft | Yes |
| `DELETE` | `/posts/{id}` | Soft-delete a post | Yes |
| `GET` | `/posts/drafts` | List all draft posts | Yes |

**Post object schema (abbreviated):**

```json
{
  "title": "string",
  "slug": "string",
  "content": "string",
  "excerpt": "string",
  "tags": ["string"],
  "status": "draft | published",
  "cover_image_url": "string",
  "published_at": "ISO 8601 datetime | null",
  "linkedin_post_url": "string | null",
  "meta_title": "string",
  "meta_description": "string"
}
```

---

### Profile

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `GET` | `/profile` | Get public profile data | No |
| `PUT` | `/profile` | Update profile (bio, skills, links) | Yes |
| `GET` | `/profile/linkedin-status` | Check last LinkedIn sync status | Yes |

---

### LinkedIn Sync

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `GET` | `/linkedin/auth` | Initiate LinkedIn OAuth 2.0 flow | Yes |
| `GET` | `/linkedin/callback` | OAuth callback — receives code from LinkedIn | No |
| `POST` | `/linkedin/sync` | Manually trigger a LinkedIn profile sync | Yes |
| `POST` | `/linkedin/share/{post_id}` | Share a published post to LinkedIn | Yes |
| `GET` | `/linkedin/token-status` | Check if LinkedIn token is valid/expired | Yes |

---

### Automation

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `GET` | `/automation/trending` | Fetch today's trending topic suggestions | Yes |
| `POST` | `/automation/generate` | Trigger blog post generation from a brief | Yes |
| `GET` | `/automation/status` | Check scheduler status and next run time | Yes |
| `POST` | `/automation/run-now` | Force-trigger the 48h automation cycle immediately | Yes |

**Generate post request body:**

```json
{
  "subject": "Why MCP is changing AI integrations",
  "brief": "Cover the protocol, real use cases, and adoption curve.",
  "tags": ["AI", "MCP", "integrations"],
  "auto_publish": false
}
```

---

### Webhooks

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `POST` | `/webhooks/post-published` | Called internally when a post is published — triggers notification email | Yes |
| `POST` | `/webhooks/brief-submitted` | Called when owner approves a brief from the topic email | Yes |

---

## 7. Automation Flow

The 48-hour content cycle:

```
┌─────────────────────────────────────────────────────────────┐
│  Every 48 hours (APScheduler)                               │
│                                                             │
│  1. trending_service.py                                     │
│     → scrapes Hacker News API                               │
│     → scrapes GitHub Trending                               │
│     → optionally fetches configured RSS feeds               │
│     → sends list to Claude for ranking & summarization      │
│                                                             │
│  2. email_service.py                                        │
│     → sends YOU an email with 3-5 topic suggestions         │
│        + a proposed brief for each                          │
│     → email contains reply instructions (choose + approve)  │
│                                                             │
│  3. You reply (or use the web UI) to approve one brief      │
│     → POST /api/v1/webhooks/brief-submitted is called       │
│                                                             │
│  4. ai_service.py                                           │
│     → sends subject + brief to Claude                       │
│     → receives full Markdown blog post                      │
│     → saves as draft BlogPost in MongoDB                    │
│                                                             │
│  5. Optional: auto_publish = true                           │
│     → publishes post, fires /webhooks/post-published        │
│     → sends YOU a notification email with excerpt + link    │
│     → optionally shares to LinkedIn                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. Authentication & Security

- The API uses **JWT (JSON Web Tokens)** for all owner/admin endpoints.
- Tokens are issued via `POST /api/v1/auth/login` and expire after 24h by default.
- LinkedIn integration uses **OAuth 2.0 Authorization Code flow** — tokens are stored encrypted in MongoDB.
- All endpoints that write data or trigger automation require a valid JWT.
- Public endpoints (`GET /posts`, `GET /profile`) are intentionally unauthenticated for SEO and frontend consumption.

Include the token in every protected request:

```
Authorization: Bearer <your-token>
```

---

## 9. Deployment

### Railway (recommended)

1. Connect your GitHub repository to a new Railway project.
2. Add all environment variables via the Railway dashboard (Variables tab).
3. Railway auto-detects the Dockerfile and builds on push to `main`.
4. Set a custom domain pointing to your Railway service URL.
5. Configure a health check on `GET /api/v1/health`.

### Docker

```bash
docker build -t smart-blog-api .
docker run -p 8000:8000 --env-file .env smart-blog-api
```

### Production checklist

- Set `APP_ENV=production`
- Set a strong, random `SECRET_KEY` (minimum 64 chars)
- Restrict `ALLOWED_ORIGINS` to your actual frontend domain only
- Enable MongoDB Atlas IP whitelisting for your server IP
- Rotate LinkedIn OAuth tokens before they expire (60-day validity)
- Monitor scheduler health via `GET /api/v1/automation/status`

---

## 10. Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run all tests
pytest

# With coverage report
pytest --cov=app --cov-report=term-missing
```

Tests use a separate test database configured via `MONGODB_DB_NAME=test_smart_blog_ai`. LinkedIn and email services are mocked in tests.

---

## 11. Contributing & Conventions

- **Branch naming:** `feature/short-description`, `fix/short-description`
- **Commits:** follow [Conventional Commits](https://www.conventionalcommits.org/) — `feat:`, `fix:`, `chore:`, `docs:`
- All new endpoints must include Pydantic schemas for both request and response
- Type hints are required on all functions
- Run `black` and `ruff` before committing

```bash
pip install black ruff
black app/
ruff check app/
```

---

*Smart Blog AI · FastAPI Backend · Built with Python, FastAPI, MongoDB Atlas & Claude*