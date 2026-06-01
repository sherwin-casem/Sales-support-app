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
