# Sales Intelligence & AI Outreach Platform

Internal sales intelligence platform — Alpha MVP.

Replace multiple sales tools with unified lead management, enrichment, AI outreach, and campaign tracking.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 15, TypeScript, Tailwind, shadcn/ui |
| Backend | FastAPI, Python 3.12, SQLAlchemy, Pydantic |
| Database | PostgreSQL 16 |
| Queue | Redis + Celery |
| Auth | JWT + RBAC (ADMIN, MANAGER, SALES) |
| AI | OpenAI API |
| Scraping | Playwright, BeautifulSoup |
| Deployment | Docker Compose |

## Project Structure

```
├── frontend/           # Next.js application
├── backend/            # FastAPI modular monolith
├── database/           # SQL migrations & seeds
├── docker/             # Dockerfiles & compose
├── docs/               # Architecture & API design
├── .env.example        # Environment template
└── docker-compose.yml  # Root compose entry
```

## Documentation

- [Architecture](docs/architecture.md)
- [API Design](docs/api-design.md)
- [Database Schema](docs/database-schema.md)

## Development Phases

| Phase | Scope | Status |
|-------|-------|--------|
| **1** | Architecture, folders, DB schema, Docker | **Complete** |
| **2** | Backend modules & APIs | **In progress** |
| 2a | Auth (JWT, RBAC, refresh tokens) | Complete |
| 2b | Leads (CRUD, CSV, decision makers) | Complete |
| 2c | Analytics (`GET /analytics/overview`) | Complete |
| 2d | Celery scaffold (`health.ping`) | Complete |
| 2e | Users, enrichment, campaigns APIs | Pending |
| 2f | Alembic baseline (`001_initial_schema`) | Complete |
| **3** | Frontend | **In progress** |
| 3a | Login, dashboard shell, KPIs, settings, dark mode | Complete |
| 3b | Leads, campaigns, analytics pages (full UI) | Complete |
| **4** | OpenAI, scraping, email integrations | Pending |

## MVP Feature Progress

| Feature | Backend | Frontend |
|---------|---------|----------|
| Authentication & RBAC | Done | Done (login) |
| Lead management | Done | Done |
| Analytics dashboard | Done | Done |
| Data enrichment | Pending | Pending |
| Decision maker detection | Pending | Pending |
| AI message generation | Pending | Pending |
| Campaign system | Pending | Pending |

## Getting Started

```bash
cp .env.docker.example .env   # Docker
# or: cp .env.local.example .env   # local dev without Docker

# Docker — recommended MVP services only
docker compose up -d postgres redis backend frontend

# Optional Celery worker
docker compose --profile worker up -d
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- OpenAPI: http://localhost:8000/docs

## License

Internal use — Alpha MVP
