# Backend

FastAPI modular monolith for the Sales Intelligence & AI Outreach Platform.

## Structure

```
backend/
├── requirements.txt
└── src/
    ├── main.py           # FastAPI app entry
    ├── auth/             # JWT, signup, login, refresh
    ├── users/            # User management, RBAC
    ├── leads/            # Lead CRUD, CSV import/export
    ├── enrichment/       # Enrichment pipeline
    ├── campaigns/        # Campaign management
    ├── scrapers/         # Web scraping (Playwright, BS4)
    ├── ai/               # OpenAI integrations
    ├── analytics/        # Dashboard metrics
    ├── jobs/             # Celery background tasks
    └── common/           # Shared config, DB, utilities
```

## Phase Status

| Phase | Status |
|-------|--------|
| 1 — Structure & Docker | Complete |
| 2 — Backend modules | In progress |
| 2a — Auth (JWT, RBAC) | Complete |
| 2b — Leads (CRUD, CSV, decision makers) | Complete |
| 2c — Analytics overview | Complete |
| 2d — Celery scaffold | Complete |
| 2e — Users, enrichment, campaigns | Pending |
| 2f — Alembic baseline (`001_initial_schema`) | Complete |

## Database migrations (Alembic)

Baseline revision `001_initial_schema` mirrors `database/migrations/001_initial_schema.sql`.

```bash
cd backend
pip install -r requirements.txt

# Fresh DB
alembic upgrade head

# Existing DB (schema already applied via SQL init)
alembic stamp head
```

See `alembic/README` for details.

## Auth Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/signup` | Register (default role SALES) |
| POST | `/api/v1/auth/login` | Login; sets httpOnly refresh cookie |
| POST | `/api/v1/auth/refresh` | Rotate access token via cookie |
| POST | `/api/v1/auth/logout` | Revoke refresh token |
| GET | `/api/v1/auth/me` | Current user profile |

Refresh token is stored hashed in `refresh_tokens` and delivered as an httpOnly cookie scoped to `/api/v1/auth`.

## Lead Endpoints

| Method | Path | Role | Description |
|--------|------|------|-------------|
| GET | `/api/v1/leads` | SALES+ | List with search, filter, pagination |
| POST | `/api/v1/leads` | SALES+ | Create lead |
| GET | `/api/v1/leads/{id}` | SALES+ | Get lead with decision makers |
| PATCH | `/api/v1/leads/{id}` | SALES+ | Update lead |
| DELETE | `/api/v1/leads/{id}` | MANAGER+ | Delete lead |
| POST | `/api/v1/leads/import` | SALES+ | CSV import |
| GET | `/api/v1/leads/export` | SALES+ | CSV export |
| GET | `/api/v1/leads/{id}/decision-makers` | SALES+ | List decision makers |
| POST | `/api/v1/leads/{id}/decision-makers` | SALES+ | Add decision maker |
| DELETE | `/api/v1/leads/{id}/decision-makers/{dm_id}` | SALES+ | Remove decision maker |

SALES users see only their own leads (`created_by`). MANAGER and ADMIN see all leads.

## Analytics Endpoints

| Method | Path | Role | Description |
|--------|------|------|-------------|
| GET | `/api/v1/analytics/overview` | SALES+ | Dashboard KPIs (leads, rates, status breakdown) |

## Celery (optional)

Minimal worker scaffold for background jobs:

```bash
# Local (requires Redis)
celery -A src.jobs.celery_app worker --loglevel=info

# Docker (optional profile)
docker compose --profile worker up -d celery-worker
```

Health check task: `health.ping` → returns `"pong"`.

## Tests

Uses **pytest**, **httpx** (`AsyncClient`), and **pytest-asyncio** with a dedicated PostgreSQL
test database and per-test transaction rollback (see `tests/conftest.py`).

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

Optional env vars:

```env
TEST_DATABASE_URL=postgresql+asyncpg://salesapp:salesapp@localhost:5432/salesapp_test
TEST_DATABASE_ADMIN_USER=postgres
TEST_DATABASE_ADMIN_PASSWORD=salesapp
```

The test suite creates `salesapp_test` if missing and applies the initial SQL migration once.
Each test runs inside a rolled-back transaction — no manual cleanup required.
Admin credentials are used only to create the test database.

## Local Development

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000
```

## API Docs

- Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
