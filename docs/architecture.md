# Sales Intelligence & AI Outreach Platform — Architecture (Alpha MVP)

## Overview

Modular monolith delivering lead management, enrichment, decision-maker detection, AI outreach, and campaign tracking. All services run via Docker Compose for local development and deployment parity.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Client (Browser)                              │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │ HTTPS
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  frontend/          Next.js 15 · TypeScript · Tailwind · shadcn/ui      │
│  - App Router pages (Login, Dashboard, Leads, Campaigns, Analytics)     │
│  - JWT stored in httpOnly cookie / memory (access) + refresh flow       │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │ REST /api/v1/*
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  backend/           FastAPI · Python 3.12 · Pydantic · SQLAlchemy       │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┬──────────┐  │
│  │   auth   │  users   │  leads   │enrichment│ campaigns│ analytics│  │
│  └──────────┴──────────┴──────────┴──────────┴──────────┴──────────┘  │
│  ┌──────────┬──────────┬──────────┬──────────┐                          │
│  │ scrapers │    ai    │   jobs   │  common  │                          │
│  └──────────┴──────────┴──────────┴──────────┘                          │
└───────────┬─────────────────────────────┬───────────────────────────────┘
            │                             │
            ▼                             ▼
┌───────────────────────┐     ┌───────────────────────┐
│  PostgreSQL           │     │  Redis                │
│  - Normalized schema  │     │  - Celery broker      │
│  - Alembic migrations │     │  - Result backend     │
└───────────────────────┘     └───────────┬───────────┘
                                          │
                                          ▼
                              ┌───────────────────────┐
                              │  Celery Worker        │
                              │  - Enrichment jobs    │
                              │  - Campaign send jobs │
                              └───────────────────────┘
```

## Design Principles

| Principle | Application |
|-----------|-------------|
| Modular monolith | Domain modules under `backend/src/` with clear boundaries; shared infra in `common/` |
| Clean architecture | Routes → Services → Repositories → Models; no business logic in route handlers |
| API-first | OpenAPI at `/docs`; versioned prefix `/api/v1` |
| Async where it matters | Celery for scraping, enrichment, email send |
| Fail closed | JWT + RBAC on all protected routes; role checks in service layer |
| MVP scope | Email sending only; LinkedIn/WhatsApp message generation without automation |

## Module Responsibilities

### `auth/`
- Signup, login, refresh token rotation
- JWT access/refresh token issuance and validation
- Password hashing (bcrypt)
- RBAC dependency injection (`require_role`)

### `users/`
- User CRUD (admin/manager)
- Profile and role assignment

### `leads/`
- Lead CRUD, CSV import/export
- Decision maker sub-resource
- Status lifecycle: NEW → ENRICHED → CONTACTED → REPLIED → CONVERTED

### `enrichment/`
- Trigger enrichment pipeline (sync preview + async full run)
- Store enrichment results linked to leads
- Orchestrate scrapers + inference

### `scrapers/`
- Playwright + BeautifulSoup website scraping
- Leadership/team/about page detection
- Domain extraction utilities

### `ai/`
- OpenAI integration for personalized messages
- Channel-specific prompts (email, LinkedIn, WhatsApp)
- Persist generated messages

### `campaigns/`
- Campaign, CampaignLead, CampaignMessage entities
- Schedule and mark-sent workflow
- Email dispatch via background job (SMTP/API TBD in Phase 4)

### `analytics/`
- Aggregated metrics: lead counts, campaign stats, reply/conversion rates
- Read-only queries optimized with indexes

### `jobs/`
- Celery app configuration
- Task definitions: `enrich_lead`, `detect_decision_makers`, `send_campaign_email`

### `common/`
- Database session, base model, timestamps mixin
- Config (Pydantic Settings), exceptions, pagination, logging

## Request Flow (Example: Enrich Lead)

```
POST /api/v1/enrichment/leads/{id}
  → auth middleware (JWT)
  → RBAC (SALES+)
  → EnrichmentService.enqueue(lead_id)
  → Celery task enrich_lead
      → Scrapers: fetch homepage metadata
      → Scrapers: find leadership pages
      → AI/heuristics: infer industry & size
      → Repository: save EnrichmentRecord, update Lead
      → Repository: upsert DecisionMakers
  → 202 Accepted { job_id }
```

## Authentication & RBAC

| Role | Permissions |
|------|-------------|
| ADMIN | Full access, user management |
| MANAGER | All sales ops, view all team data |
| SALES | Own leads/campaigns; read shared where assigned |

Tokens:
- **Access token**: short-lived (15 min), Bearer header
- **Refresh token**: long-lived (7 days), httpOnly cookie, stored hashed in DB

## Frontend Architecture

```
frontend/
├── app/              # Next.js App Router pages & layouts
├── components/       # Shared UI (shadcn wrappers, layout, tables)
├── features/         # Feature slices (leads, campaigns, auth)
├── lib/              # Utils, hooks, theme provider
├── services/       # API client (fetch wrapper + typed endpoints)
└── types/          # Shared TypeScript interfaces mirroring API schemas
```

- Server Components for static shells; Client Components for interactive tables/forms
- TanStack Query (or SWR) for data fetching in Phase 3
- Dark mode via `next-themes` + Tailwind `dark:` variants

## External Integrations (Phase 4)

| Service | Purpose |
|---------|---------|
| OpenAI API | Message generation |
| SMTP / SendGrid | Email campaign delivery |
| Playwright | Headless browser scraping |

## Deployment Topology (Docker Compose)

| Service | Image | Port |
|---------|-------|------|
| frontend | `docker/frontend/Dockerfile` | 3000 |
| backend | `docker/backend/Dockerfile` | 8000 |
| celery-worker | same backend image | — |
| postgres | `postgres:16-alpine` | 5432 |
| redis | `redis:7-alpine` | 6379 |

Health checks on backend (`/health`) and postgres readiness gate for migrations.

## Phase Roadmap

| Phase | Scope | Status |
|-------|-------|--------|
| 1 | Architecture, folders, DB schema, Docker | **Complete** |
| 2 | Backend modules & APIs | **In progress** |
| 2a | Auth, leads, analytics, Celery scaffold | Complete |
| 2b | Users, enrichment, campaigns | Pending |
| 2c | Alembic baseline (`001_initial_schema`) | Complete |
| 3 | Frontend | **In progress** |
| 3a | Login, dashboard, settings | Complete |
| 3b | Leads, campaigns, analytics pages | Pending |
| 4 | OpenAI, scraping, email integrations | Pending |

## Open Decisions (Require Approval Before Change)

1. **Email provider**: SMTP vs SendGrid — default SMTP via env for MVP
2. **Multi-tenancy**: Single org with RBAC (no tenant_id) for Alpha
3. **Lead ownership**: `created_by` FK; managers see all, sales see own
4. **Refresh token storage**: Hashed in `refresh_tokens` table with revocation
