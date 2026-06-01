# Docker

Container definitions and Compose configuration for all services.

## Services

| Service | Container | Port | Description |
|---------|-----------|------|-------------|
| postgres | sales-postgres | 5432 | PostgreSQL 16 with auto-init schema |
| redis | sales-redis | 6379 | Celery broker & cache |
| backend | sales-backend | 8000 | FastAPI API server |
| celery-worker | sales-celery-worker | — | Background job processor |
| frontend | sales-frontend | 3000 | Next.js app |

## Quick Start

```bash
# From project root
cp .env.example .env

# Start all services (Phase 2+ when backend/frontend are ready)
docker compose up -d

# View logs
docker compose logs -f backend

# Stop
docker compose down
```

## Files

```
docker/
├── docker-compose.yml    # Full stack definition
├── backend/Dockerfile    # Python 3.12 + FastAPI
├── frontend/Dockerfile   # Node 20 + Next.js 15
└── postgres/init-db.sh   # Optional manual migration script
```

Root `docker-compose.yml` includes `docker/docker-compose.yml`.

## Notes

- Postgres auto-applies `database/migrations/001_initial_schema.sql` on first boot via `docker-entrypoint-initdb.d`.
- Backend and Celery share the same image with different commands.
- Development targets mount source code for hot reload.
