# Database

PostgreSQL schema and migration scripts for the Sales Intelligence platform.

## Structure

```
database/
├── migrations/
│   ├── 001_initial_schema.sql       # Up migration
│   └── 001_initial_schema.down.sql  # Down migration
└── seeds/                           # Seed data (Phase 2)
```

## Apply Migration (Manual)

With Postgres running via Docker Compose:

```bash
docker compose exec postgres psql -U salesapp -d salesapp -f /docker-entrypoint-initdb.d/001_initial_schema.sql
```

Or connect locally:

```bash
psql postgresql://salesapp:salesapp@localhost:5432/salesapp -f database/migrations/001_initial_schema.sql
```

## Alembic (Phase 2)

Alembic will be configured in `backend/` to manage migrations programmatically. SQL files here serve as the canonical schema reference for Phase 1.
