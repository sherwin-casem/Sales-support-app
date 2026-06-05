"""Lead search runs for intent-driven find-leads flow.

Revision ID: 003_lead_search_runs
Revises: 002_discovery_enrichment
Create Date: 2026-06-04

"""

from __future__ import annotations

from alembic import op
from sqlalchemy import text

from src.common.sql_migration import iter_sql_statements, migration_sql_path

revision = "003_lead_search_runs"
down_revision = "002_discovery_enrichment"
branch_labels = None
depends_on = None


def upgrade() -> None:
    sql = migration_sql_path("003_lead_search_runs.sql").read_text(encoding="utf-8")
    for statement in iter_sql_statements(sql):
        op.execute(text(statement))


def downgrade() -> None:
    sql = migration_sql_path("003_lead_search_runs.down.sql").read_text(encoding="utf-8")
    for statement in iter_sql_statements(sql):
        op.execute(text(statement))
