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

## Local Development (Phase 2+)

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
