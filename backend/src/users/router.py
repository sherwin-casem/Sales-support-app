from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_minimum_role, require_roles
from src.common.database import get_db
from src.common.enums import UserRole
from src.common.pagination import PaginatedResponse
from src.users.models import User
from src.users.schemas import UserListResponse, UserUpdate
from src.users.service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=PaginatedResponse[UserListResponse])
async def list_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER))],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginatedResponse[UserListResponse]:
    return await UserService(db).list_users(current_user, page=page, page_size=page_size)


@router.get("/{user_id}", response_model=UserListResponse)
async def get_user(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER))],
) -> UserListResponse:
    return await UserService(db).get_user(current_user, user_id)


@router.patch("/{user_id}", response_model=UserListResponse)
async def update_user(
    user_id: UUID,
    payload: UserUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_minimum_role(UserRole.ADMIN))],
) -> UserListResponse:
    return await UserService(db).update_user(current_user, user_id, payload)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_minimum_role(UserRole.ADMIN))],
) -> None:
    await UserService(db).deactivate_user(current_user, user_id)
