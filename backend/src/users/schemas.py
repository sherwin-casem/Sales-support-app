import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.common.enums import UserRole


class UserUpdate(BaseModel):
    role: UserRole | None = None
    is_active: bool | None = None
    full_name: str | None = Field(default=None, min_length=1, max_length=255)


class UserListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool


class UserDetailResponse(UserListResponse):
    created_at: str | None = None
