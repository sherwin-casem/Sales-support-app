"""Discovery profiles, crawl runs, lead extensions, intent signals.

Revision ID: 002_discovery_enrichment
Revises: 001_initial_schema
Create Date: 2026-06-04

"""

from __future__ import annotations

from alembic import op
from sqlalchemy import text

from src.common.sql_migration import iter_sql_statements, migration_sql_path

revision = "002_discovery_enrichment"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    sql = migration_sql_path("002_discovery_enrichment.sql").read_text(encoding="utf-8")
    for statement in iter_sql_statements(sql):
        op.execute(text(statement))


def downgrade() -> None:
    sql = migration_sql_path("002_discovery_enrichment.down.sql").read_text(encoding="utf-8")
    for statement in iter_sql_statements(sql):
        op.execute(text(statement))
