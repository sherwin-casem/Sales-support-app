"""Helpers for executing canonical SQL migration files."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
MIGRATIONS_DIR = REPO_ROOT / "database" / "migrations"


def migration_sql_path(name: str) -> Path:
    return MIGRATIONS_DIR / name


def iter_sql_statements(content: str) -> Iterator[str]:
    """Split a SQL migration file into executable statements."""
    buffer: list[str] = []
    in_dollar_quote = False

    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("--") or not stripped:
            continue

        if "$$" in line and line.count("$$") % 2 == 1:
            in_dollar_quote = not in_dollar_quote

        buffer.append(line)
        if not in_dollar_quote and stripped.endswith(";"):
            statement = "\n".join(buffer).strip()
            if statement:
                yield statement
            buffer = []

    trailing = "\n".join(buffer).strip()
    if trailing:
        yield trailing
