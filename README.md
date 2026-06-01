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
| 2 | Backend modules, API, Alembic migrations | Pending |
| 3 | Frontend pages & features | Pending |
| 4 | OpenAI, scraping, email integrations | Pending |

## Getting Started (Phase 2+)

```bash
cp .env.example .env
docker compose up -d
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- OpenAPI: http://localhost:8000/docs

## MVP Features

1. Lead Management (CRUD, CSV import/export)
2. Data Enrichment (website scraping pipeline)
3. Decision Maker Identification
4. AI Message Generation (email, LinkedIn, WhatsApp copy)
5. Campaign System (email sending only)
6. Analytics Dashboard
7. Authentication & Multi-user RBAC

## License

Internal use — Alpha MVP
