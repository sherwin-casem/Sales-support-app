from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import RefreshToken
from src.auth.schemas import AuthResponse, LoginRequest, SignupRequest, TokenResponse, UserResponse
from src.auth.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_token,
    refresh_token_expires_at,
    verify_password,
)
from src.common.config import Settings, get_settings
from src.common.enums import UserRole
from src.common.exceptions import ConflictException, UnauthorizedException
from src.users.models import User


class AuthService:
    def __init__(self, db: AsyncSession, settings: Settings | None = None) -> None:
        self.db = db
        self.settings = settings or get_settings()

    async def signup(self, payload: SignupRequest) -> tuple[AuthResponse, str]:
        existing = await self.db.scalar(select(User).where(User.email == payload.email.lower()))
        if existing:
            raise ConflictException("Email already registered", code="EMAIL_EXISTS")

        user = User(
            email=payload.email.lower(),
            password_hash=hash_password(payload.password),
            full_name=payload.full_name.strip(),
            role=UserRole.SALES,
            is_active=True,
        )
        self.db.add(user)
        await self.db.flush()

        access_token, expires_in = create_access_token(
            user_id=user.id,
            role=user.role.value,
            settings=self.settings,
        )
        refresh_token = await self._persist_refresh_token(user.id)

        return (
            AuthResponse(
                access_token=access_token,
                expires_in=expires_in,
                user=UserResponse.model_validate(user),
            ),
            refresh_token,
        )

    async def login(self, payload: LoginRequest) -> tuple[AuthResponse, str]:
        user = await self.db.scalar(select(User).where(User.email == payload.email.lower()))
        if user is None or not verify_password(payload.password, user.password_hash):
            raise UnauthorizedException("Invalid email or password", code="INVALID_CREDENTIALS")

        if not user.is_active:
            raise UnauthorizedException("Account is inactive", code="ACCOUNT_INACTIVE")

        access_token, expires_in = create_access_token(
            user_id=user.id,
            role=user.role.value,
            settings=self.settings,
        )
        refresh_token = await self._persist_refresh_token(user.id)

        return (
            AuthResponse(
                access_token=access_token,
                expires_in=expires_in,
                user=UserResponse.model_validate(user),
            ),
            refresh_token,
        )

    async def refresh(self, raw_refresh_token: str) -> tuple[TokenResponse, str]:
        token_hash = hash_token(raw_refresh_token)
        record = await self.db.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )

        if record is None or record.revoked_at is not None:
            raise UnauthorizedException("Invalid refresh token", code="INVALID_REFRESH_TOKEN")

        if record.expires_at.tzinfo is None:
            expires_at = record.expires_at.replace(tzinfo=UTC)
        else:
            expires_at = record.expires_at

        if expires_at < datetime.now(UTC):
            raise UnauthorizedException("Refresh token expired", code="REFRESH_TOKEN_EXPIRED")

        user = await self.db.get(User, record.user_id)
        if user is None or not user.is_active:
            raise UnauthorizedException("Account is inactive", code="ACCOUNT_INACTIVE")

        record.revoked_at = datetime.now(UTC)
        new_refresh_token = await self._persist_refresh_token(user.id)

        access_token, expires_in = create_access_token(
            user_id=user.id,
            role=user.role.value,
            settings=self.settings,
        )

        return (
            TokenResponse(access_token=access_token, expires_in=expires_in),
            new_refresh_token,
        )

    async def logout(self, raw_refresh_token: str | None) -> None:
        if not raw_refresh_token:
            return

        token_hash = hash_token(raw_refresh_token)
        record = await self.db.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        if record and record.revoked_at is None:
            record.revoked_at = datetime.now(UTC)

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        return await self.db.get(User, user_id)

    async def _persist_refresh_token(self, user_id: UUID) -> str:
        raw_token = generate_refresh_token()
        record = RefreshToken(
            user_id=user_id,
            token_hash=hash_token(raw_token),
            expires_at=refresh_token_expires_at(self.settings),
        )
        self.db.add(record)
        await self.db.flush()
        return raw_token
