# Database

PostgreSQL schema and migration scripts for the Sales Intelligence platform.

## Structure

```
database/
├── migrations/
│   ├── 001_initial_schema.sql       # Canonical up migration (source of truth)
│   └── 001_initial_schema.down.sql  # Canonical down migration
└── seeds/                           # Seed data (Phase 2)
```

## Alembic (recommended)

Alembic lives in `backend/alembic/` and baseline revision `001_initial_schema` executes the
SQL files above without duplicating schema logic.

```bash
cd backend

# Fresh database
alembic upgrade head

# Database already initialized from 001_initial_schema.sql (Docker init, manual psql, etc.)
alembic stamp head
```

## Manual SQL (legacy / Docker init)

Docker Compose still mounts the SQL file into Postgres `docker-entrypoint-initdb.d` on first boot.
After that, stamp Alembic so revision history matches:

```bash
docker compose exec backend alembic stamp head
```

Or apply manually:

```bash
psql postgresql://salesapp:salesapp@localhost:5432/salesapp -f database/migrations/001_initial_schema.sql
cd backend && alembic stamp head
```
