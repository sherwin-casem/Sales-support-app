# Folder Structure

Generated in Phase 1. Module implementations follow in Phases 2–4.

```
GEO-AEO-SEO-sales-support-app/
│
├── .env.example                 # Environment variable template
├── .gitignore
├── docker-compose.yml           # Root compose (includes docker/docker-compose.yml)
├── README.md
│
├── docs/
│   ├── architecture.md          # System architecture & module boundaries
│   ├── api-design.md            # REST API specification (/api/v1)
│   └── database-schema.md       # ERD, tables, indexes, enums
│
├── database/
│   ├── README.md
│   ├── migrations/
│   │   ├── 001_initial_schema.sql
│   │   └── 001_initial_schema.down.sql
│   └── seeds/                   # Phase 2
│
├── docker/
│   ├── README.md
│   ├── docker-compose.yml       # Full stack: postgres, redis, backend, celery, frontend
│   ├── backend/
│   │   └── Dockerfile
│   ├── frontend/
│   │   └── Dockerfile
│   └── postgres/
│       └── init-db.sh
│
├── backend/
│   ├── README.md
│   ├── requirements.txt
│   └── src/
│       ├── main.py              # FastAPI entry (health check stub)
│       ├── auth/
│       ├── users/
│       ├── leads/
│       ├── enrichment/
│       ├── campaigns/
│       ├── scrapers/
│       ├── ai/
│       ├── analytics/
│       ├── jobs/
│       └── common/
│
└── frontend/
    ├── README.md
    ├── package.json             # Stub — Phase 3 installs Next.js 15
    ├── app/                     # App Router pages
    ├── components/              # shadcn/ui + shared components
    ├── features/                # Feature slices
    ├── lib/                     # Utils, hooks, theme
    ├── services/                # API client
    └── types/                   # TypeScript interfaces
```

## Backend Module Map

| Module | Responsibility | Phase |
|--------|----------------|-------|
| `auth` | JWT, signup, login, refresh | 2 |
| `users` | User CRUD, role assignment | 2 |
| `leads` | Lead CRUD, CSV, decision makers | 2 |
| `enrichment` | Enrichment pipeline orchestration | 2 |
| `campaigns` | Campaign lifecycle, scheduling | 2 |
| `analytics` | Dashboard KPIs | 2 |
| `jobs` | Celery task definitions | 2 |
| `common` | Config, DB session, shared utils | 2 |
| `scrapers` | Playwright + BeautifulSoup | 4 |
| `ai` | OpenAI message generation | 4 |

## Frontend Feature Map (Phase 3)

| Path | Page |
|------|------|
| `/login` | Authentication |
| `/dashboard` | Overview KPIs |
| `/leads` | Lead management |
| `/campaigns` | Campaign management |
| `/analytics` | Metrics & charts |
| `/settings` | Profile, theme |
