from collections.abc import Callable
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.rbac import has_any_role, has_minimum_role
from src.auth.security import decode_access_token
from src.common.database import get_db
from src.common.enums import UserRole
from src.common.exceptions import ForbiddenException, UnauthorizedException
from src.users.models import User

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedException("Missing or invalid authorization header", code="MISSING_TOKEN")

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = UUID(payload["sub"])
    except (ValueError, KeyError):
        raise UnauthorizedException("Invalid or expired access token", code="INVALID_TOKEN") from None

    user = await db.get(User, user_id)
    if user is None:
        raise UnauthorizedException("User not found", code="USER_NOT_FOUND")

    if not user.is_active:
        raise UnauthorizedException("Account is inactive", code="ACCOUNT_INACTIVE")

    return user


async def get_optional_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User | None:
    if credentials is None:
        return None
    try:
        return await get_current_user(credentials, db)
    except UnauthorizedException:
        return None


def require_roles(*roles: UserRole) -> Callable:
    allowed = set(roles)

    async def dependency(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if not has_any_role(current_user.role, allowed):
            raise ForbiddenException(
                f"Requires one of: {', '.join(role.value for role in roles)}",
                code="INSUFFICIENT_ROLE",
            )
        return current_user

    return dependency


def require_minimum_role(minimum_role: UserRole) -> Callable:
    async def dependency(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if not has_minimum_role(current_user.role, minimum_role):
            raise ForbiddenException(
                f"Requires minimum role: {minimum_role.value}",
                code="INSUFFICIENT_ROLE",
            )
        return current_user

    return dependency
