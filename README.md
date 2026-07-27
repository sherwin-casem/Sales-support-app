# Sales Intelligence & AI Outreach Platform

Web platform for automatic lead discovery, enrichment, verification, campaigns, and AI outreach.

## Features (Scope items 7–17)

| # | Feature | Status |
|---|---------|--------|
| 7 | Data enrichment | Done |
| 8 | Decision maker identification | Done (scrape + OpenAI) |
| 9 | Email verification (OSS) | Done (format + MX) |
| 10 | Phone verification (OSS) | Done (format validation) |
| 11 | Multi-channel outreach | Email send + LinkedIn/WhatsApp copy export |
| 12 | AI message generation | Done |
| 13 | Scheduled scraping | Celery Beat + discovery profiles |
| 14 | Duplicate removal | Done |
| 15 | Intent signal detection | Done |
| 16 | Campaign performance tracking | Done |
| 17 | Multi-user RBAC | Done + admin UI |

## Tech Stack

Next.js 15 · FastAPI · PostgreSQL 16 · Redis · Celery · OpenAI · Playwright/BeautifulSoup

## Quick Start

```bash
cp .env.docker.example .env
docker compose up -d postgres redis backend frontend
docker compose --profile worker up -d   # discovery + enrichment workers
```

- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs

## Documentation

- [Installation (Parijat server)](docs/installation.md)
- [Operations](docs/operations.md)
- [Third-party services](docs/third-party.md)
- [Architecture](docs/architecture.md)
- [API Design](docs/api-design.md)

## Tests

```bash
cd backend
pip install -r requirements.txt -r requirements-dev.txt
pytest
```
