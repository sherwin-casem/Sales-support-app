import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models import User


@pytest.mark.asyncio
async def test_signup_persists_within_test_and_rolls_back(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    email = f"test-{uuid.uuid4()}@example.com"
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": "password123",
            "full_name": "Test User",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["user"]["email"] == email
    assert body["access_token"]

    count = await db_session.scalar(select(func.count()).select_from(User))
    assert count == 1
