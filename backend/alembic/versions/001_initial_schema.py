"""Initial schema baseline from database/migrations/001_initial_schema.sql

This revision mirrors the canonical SQL migration. It does not change an
existing database that was already initialized from the same SQL file —
use ``alembic stamp head`` in that case.

Revision ID: 001_initial_schema
Revises:
Create Date: 2026-06-04

"""

from __future__ import annotations

from alembic import op
from sqlalchemy import text

from src.common.sql_migration import iter_sql_statements, migration_sql_path

revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    sql = migration_sql_path("001_initial_schema.sql").read_text(encoding="utf-8")
    for statement in iter_sql_statements(sql):
        op.execute(text(statement))


def downgrade() -> None:
    sql = migration_sql_path("001_initial_schema.down.sql").read_text(encoding="utf-8")
    for statement in iter_sql_statements(sql):
        op.execute(text(statement))
