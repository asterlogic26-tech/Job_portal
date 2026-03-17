# Personal AI Job Agent

A single-user AI-powered job search command center. Discovers jobs automatically, scores them against your profile, generates cover letters and outreach emails, and tracks every application — all from a single dashboard.

---

## Quick Start

### Prerequisites

- Docker 24+ and Docker Compose v2
- An Anthropic API key (`claude-sonnet-4-6` is the default model)

### 1. Configure environment

```bash
cp .env.example .env
# Edit .env and set at minimum:
#   ANTHROPIC_API_KEY=sk-ant-...
#   SECRET_KEY=<random 32+ chars>
```

### 2. Start all services

```bash
docker compose up
```

On first boot, Alembic migrations run automatically, seeding the single-user row and all tables.

### 3. Open the dashboard

| Service | URL |
|---------|-----|
| Dashboard (UI) | http://localhost:3000 |
| API docs (Swagger) | http://localhost:8000/docs |
| Flower (Celery monitor) | http://localhost:5555 |
| MinIO console | http://localhost:9001 |

Default Flower credentials: `admin / admin` (set via `FLOWER_USER` / `FLOWER_PASSWORD`).

---

## Architecture

```
personal-job-agent/
├── backend/          FastAPI async API (PYTHONPATH root: /app)
│   ├── api/          Route handlers (v1)
│   ├── core/         Config, logging, exceptions
│   ├── db/           SQLAlchemy models, Alembic migrations, session
│   ├── models/       ORM table definitions (11 tables)
│   ├── schemas/      Pydantic request/response schemas
│   └── services/     Business logic layer
│
├── workers/          Celery workers + Beat scheduler
│   ├── tasks/        8 task modules (discovery, matching, radar, …)
│   ├── celery_app.py Celery factory
│   └── beat_schedule.py Periodic task schedule
│
├── engines/          Pure-Python AI/ML engines (no DB dependency)
│   ├── matching/     Skill, seniority, salary, recency scorers
│   ├── embedding/    sentence-transformers embedder + Qdrant store
│   ├── normalization/ Title normalizer, deduplicator, extractor
│   ├── content/      LLM cover letter / email generator
│   ├── company_radar/ Signal collector (funding, news, hiring)
│   └── predictor/   Interview probability predictor
│
├── crawlers/         Scrapy spiders (LinkedIn, Indeed, …)
├── integrations/     External API clients (Crunchbase, Hunter.io, …)
├── frontend/         React + TypeScript + Tailwind (Vite)
├── database/init/    Postgres init SQL (extensions, schemas)
├── infrastructure/   Docker configs (nginx, redis.conf)
├── tests/            Unit tests (pytest + pytest-asyncio)
└── docker-compose.yml
```

### Key design decisions

| Decision | Rationale |
|----------|-----------|
| Single fixed user ID `00000000-0000-0000-0000-000000000001` | Personal-use tool — no auth overhead |
| `PYTHONPATH=/app` (project root) | All packages (`backend`, `workers`, `engines`, `crawlers`, `integrations`) importable as top-level |
| Celery task names use full path `workers.tasks.xxx.fn` | Prevents import ambiguity when project root is `/app` |
| Block detection → `ManualTask` DB record | Hard contract: **never** bypass CAPTCHA / anti-bot; user completes manually |
| Qdrant for vector search | Fast ANN search for job ↔ profile semantic similarity |
| sentence-transformers `all-MiniLM-L6-v2` | 384-dim embeddings, runs on CPU without GPU |

---

## Services

| Container | Role | Port |
|-----------|------|------|
| `postgres` | PostgreSQL 16 + pgvector | 5432 |
| `redis` | Broker + result backend for Celery | 6379 |
| `qdrant` | Vector store for semantic search | 6333 |
| `minio` | Object storage for résumé files | 9000 / 9001 |
| `backend` | FastAPI (uvicorn, --reload in dev) | 8000 |
| `worker` | Celery worker (all queues) | — |
| `celery-beat` | Celery Beat scheduler | — |
| `flower` | Celery monitoring UI | 5555 |
| `frontend` | Vite dev server / nginx (prod) | 3000 |

### Celery queues

| Queue | Task type |
|-------|-----------|
| `discovery` | Job scraping from job boards |
| `matching` | Score jobs against user profile |
| `normalization` | Deduplicate + normalize raw job data |
| `radar` | Company signal collection (funding, news) |
| `content` | LLM content generation (cover letters, emails) |
| `notifications` | Email / in-app notification dispatch |
| `default` | Profile health, misc cleanup |

---

## Database schema

11 tables — all with `created_at` / `updated_at` timestamps:

- `user_profile` — single row (pre-seeded)
- `jobs` — discovered job postings
- `job_matches` — per-job match scores vs. user profile
- `applications` — application pipeline tracker
- `companies` — company profiles & radar metrics
- `company_signals` — funding rounds, news, hiring signals
- `content` — AI-generated cover letters & emails
- `notifications` — in-app + email notifications
- `manual_tasks` — tasks requiring human action (CAPTCHA, etc.)
- `recruiter_contacts` — recruiter CRM
- `network_connections` — personal network for referrals

Migrations live in `backend/db/migrations/versions/`. Run manually with:

```bash
docker compose exec backend alembic -c backend/alembic.ini upgrade head
```

---

## Development

### Run tests

```bash
# Inside backend container or with local venv
pip install -r backend/requirements.txt
pytest tests/ -v --tb=short
```

### Run linter

```bash
ruff check .
```

### Apply new migration after model changes

```bash
docker compose exec backend \
  alembic -c backend/alembic.ini revision --autogenerate -m "describe change"
docker compose exec backend \
  alembic -c backend/alembic.ini upgrade head
```

### Trigger tasks manually

```bash
# Discover new jobs
curl -X POST http://localhost:8000/api/v1/jobs/trigger-discovery

# Re-score all jobs
curl -X POST http://localhost:8000/api/v1/jobs/trigger-match-all
```

---

## Environment variables

Copy `.env.example` to `.env`. Key variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | *(required)* | Primary LLM provider |
| `OPENAI_API_KEY` | *(optional)* | Fallback LLM provider |
| `SECRET_KEY` | `change-me-in-production-please` | App secret — **change in production** |
| `DATABASE_URL` | `postgresql+asyncpg://…` | Async SQLAlchemy URL |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis URL |
| `MINIO_ENDPOINT` | `localhost:9000` | MinIO host:port (no scheme) |
| `ENABLE_QDRANT` | `true` | Toggle Qdrant vector store |
| `ENABLE_LLM` | `true` | Toggle LLM calls |
| `MATCH_SCORE_THRESHOLD` | `50` | Minimum score to surface job (0-100) |
| `HIGH_MATCH_THRESHOLD` | `75` | Score to classify as "high match" |
| `NOTIFICATION_EMAIL` | *(optional)* | Where to send email digests |

See `.env.example` for the full list.

---

## Anti-scraping contract

The crawler system will **never** attempt to bypass CAPTCHA or anti-bot protections. When a block is detected, a `ManualTask` record is created with instructions for the user to complete the action manually. This is a hard architectural constraint enforced throughout the codebase.
