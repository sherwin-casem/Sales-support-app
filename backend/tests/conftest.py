"""
Pytest fixtures for async FastAPI + PostgreSQL tests.

Uses a dedicated test database and rolls back each test via a connection-level
transaction so the database stays clean between tests.

Environment:
    TEST_DATABASE_URL — defaults to salesapp_test on localhost
"""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator, Iterator
from pathlib import Path

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from src.common.database import get_db
from src.main import app

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT.parent
MIGRATION_SQL_FILES = [
    REPO_ROOT / "database" / "migrations" / "001_initial_schema.sql",
    REPO_ROOT / "database" / "migrations" / "002_discovery_enrichment.sql",
    REPO_ROOT / "database" / "migrations" / "003_lead_search_runs.sql",
]

# Table used to detect whether each migration has been applied to the test DB.
MIGRATION_SENTINEL_TABLES = ["users", "discovery_profiles", "lead_search_runs"]

DEFAULT_TEST_DATABASE_URL = "postgresql+asyncpg://salesapp:salesapp@localhost:5432/salesapp_test"
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", DEFAULT_TEST_DATABASE_URL)
TEST_DATABASE_ADMIN_USER = os.getenv("TEST_DATABASE_ADMIN_USER", "postgres")
TEST_DATABASE_ADMIN_PASSWORD = os.getenv("TEST_DATABASE_ADMIN_PASSWORD", "salesapp")


def _iter_sql_statements(content: str) -> Iterator[str]:
    """Split a SQL migration file into executable statements."""
    buffer: list[str] = []
    in_dollar_quote = False

    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("--") or not stripped:
            continue

        if "$$" in line:
            dollar_count = line.count("$$")
            if dollar_count % 2 == 1:
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


def _admin_database_url(test_url: str) -> str:
    url = make_url(test_url)
    return (
        url.set(
            database="postgres",
            username=TEST_DATABASE_ADMIN_USER,
            password=TEST_DATABASE_ADMIN_PASSWORD,
        )
        .render_as_string(hide_password=False)
    )


async def _ensure_test_database_exists(test_url: str) -> None:
    url = make_url(test_url)
    db_name = url.database
    if not db_name:
        raise ValueError("TEST_DATABASE_URL must include a database name")

    admin_engine = create_async_engine(
        _admin_database_url(test_url),
        isolation_level="AUTOCOMMIT",
        pool_pre_ping=True,
    )
    try:
        async with admin_engine.connect() as connection:
            exists = await connection.scalar(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": db_name},
            )
            if not exists:
                await connection.execute(text(f'CREATE DATABASE "{db_name}" OWNER {url.username}'))
    finally:
        await admin_engine.dispose()


async def _table_exists(engine: AsyncEngine, table_name: str) -> bool:
    async with engine.connect() as connection:
        result = await connection.scalar(
            text("SELECT to_regclass(:name) IS NOT NULL"),
            {"name": f"public.{table_name}"},
        )
        return bool(result)


async def _apply_pending_migrations(engine: AsyncEngine) -> None:
    for migration_path, sentinel in zip(MIGRATION_SQL_FILES, MIGRATION_SENTINEL_TABLES, strict=True):
        if await _table_exists(engine, sentinel):
            continue
        if not migration_path.exists():
            raise FileNotFoundError(f"Migration file not found: {migration_path}")
        async with engine.begin() as connection:
            sql = migration_path.read_text(encoding="utf-8")
            for statement in _iter_sql_statements(sql):
                await connection.execute(text(statement))


@pytest_asyncio.fixture(scope="session")
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    await _ensure_test_database_exists(TEST_DATABASE_URL)

    engine = create_async_engine(
        TEST_DATABASE_URL,
        pool_pre_ping=True,
        echo=False,
    )

    await _apply_pending_migrations(engine)

    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_connection(test_engine: AsyncEngine) -> AsyncGenerator[AsyncConnection, None]:
    async with test_engine.connect() as connection:
        transaction = await connection.begin()
        try:
            yield connection
        finally:
            await transaction.rollback()


@pytest_asyncio.fixture
async def db_session(db_connection: AsyncConnection) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(
        bind=db_connection,
        class_=AsyncSession,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as http_client:
        yield http_client
    app.dependency_overrides.clear()
