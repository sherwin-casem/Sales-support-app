from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user
from src.auth.schemas import AuthResponse, LoginRequest, SignupRequest, TokenResponse, UserResponse
from src.auth.service import AuthService
from src.common.config import Settings, get_settings
from src.common.database import get_db
from src.common.exceptions import UnauthorizedException
from src.users.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_refresh_cookie(response: Response, token: str, settings: Settings) -> None:
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=token,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path=f"{settings.api_v1_prefix}/auth",
    )


def _clear_refresh_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        key=settings.refresh_cookie_name,
        path=f"{settings.api_v1_prefix}/auth",
    )


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    payload: SignupRequest,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthResponse:
    service = AuthService(db, settings)
    auth_response, refresh_token = await service.signup(payload)
    _set_refresh_cookie(response, refresh_token, settings)
    return auth_response


@router.post("/login", response_model=AuthResponse)
async def login(
    payload: LoginRequest,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthResponse:
    service = AuthService(db, settings)
    auth_response, refresh_token = await service.login(payload)
    _set_refresh_cookie(response, refresh_token, settings)
    return auth_response


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token_route(
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenResponse:
    raw_token = request.cookies.get(settings.refresh_cookie_name)
    if not raw_token:
        raise UnauthorizedException("Refresh token missing", code="MISSING_REFRESH_TOKEN")

    service = AuthService(db, settings)
    token_response, new_refresh_token = await service.refresh(raw_token)
    _set_refresh_cookie(response, new_refresh_token, settings)
    return token_response


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    _current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    raw_token = request.cookies.get(settings.refresh_cookie_name)
    service = AuthService(db, settings)
    await service.logout(raw_token)
    _clear_refresh_cookie(response, settings)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: Annotated[User, Depends(get_current_user)]) -> UserResponse:
    return UserResponse.model_validate(current_user)
