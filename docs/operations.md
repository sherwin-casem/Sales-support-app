# Operations Guide

## Services

| Container | Purpose |
|-----------|---------|
| sales-postgres | PostgreSQL 16 |
| sales-redis | Celery broker + result backend |
| sales-backend | FastAPI API |
| sales-frontend | Next.js UI |
| sales-celery-worker | Discovery crawl, enrichment, email send |
| sales-celery-beat | Daily stale-lead refresh |

## Logs

```bash
docker compose logs -f backend
docker compose logs -f celery-worker
docker compose logs -f celery-beat
```

## Backups

```bash
docker exec sales-postgres pg_dump -U salesapp salesapp > backup_$(date +%F).sql
```

## Migrations

New installs apply SQL from `database/migrations/` on first Postgres boot.

Existing volumes:

```bash
cd backend
alembic upgrade head
```

## Scheduled jobs

- **Celery Beat**: `discovery.refresh_stale_leads` daily (re-enriches leads older than 30 days)
- **Discovery profiles**: optional `schedule_cron` on profile (future: wire to Beat per profile)

## Scaling

- Increase Celery workers: `docker compose --profile worker up -d --scale celery-worker=2`
- Production backend: use Dockerfile `production` target with multiple uvicorn workers
