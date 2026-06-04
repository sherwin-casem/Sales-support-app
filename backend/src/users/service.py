import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.rbac import has_minimum_role
from src.common.enums import UserRole
from src.common.exceptions import ForbiddenException, NotFoundException
from src.common.pagination import PaginatedResponse
from src.users.models import User
from src.users.schemas import UserListResponse, UserUpdate


class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_users(
        self, current_user: User, *, page: int = 1, page_size: int = 20
    ) -> PaginatedResponse[UserListResponse]:
        if not has_minimum_role(current_user.role, UserRole.MANAGER):
            raise ForbiddenException("Requires manager role", code="INSUFFICIENT_ROLE")

        from sqlalchemy import func

        total = await self.db.scalar(select(func.count()).select_from(User)) or 0
        users = (
            await self.db.scalars(
                select(User).order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
            )
        ).all()
        items = [UserListResponse.model_validate(u) for u in users]
        return PaginatedResponse.build(items, total, page, page_size)

    async def get_user(self, current_user: User, user_id: uuid.UUID) -> UserListResponse:
        if not has_minimum_role(current_user.role, UserRole.MANAGER):
            raise ForbiddenException("Requires manager role", code="INSUFFICIENT_ROLE")
        user = await self.db.get(User, user_id)
        if user is None:
            raise NotFoundException("User not found", code="USER_NOT_FOUND")
        return UserListResponse.model_validate(user)

    async def update_user(self, current_user: User, user_id: uuid.UUID, payload: UserUpdate) -> UserListResponse:
        if current_user.role != UserRole.ADMIN:
            raise ForbiddenException("Requires admin role", code="INSUFFICIENT_ROLE")
        user = await self.db.get(User, user_id)
        if user is None:
            raise NotFoundException("User not found", code="USER_NOT_FOUND")
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        await self.db.flush()
        await self.db.refresh(user)
        return UserListResponse.model_validate(user)

    async def deactivate_user(self, current_user: User, user_id: uuid.UUID) -> None:
        if current_user.role != UserRole.ADMIN:
            raise ForbiddenException("Requires admin role", code="INSUFFICIENT_ROLE")
        if current_user.id == user_id:
            raise ForbiddenException("Cannot deactivate yourself", code="FORBIDDEN")
        user = await self.db.get(User, user_id)
        if user is None:
            raise NotFoundException("User not found", code="USER_NOT_FOUND")
        user.is_active = False
