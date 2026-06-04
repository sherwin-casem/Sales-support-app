from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import get_current_user, require_minimum_role
from src.common.database import get_db
from src.common.enums import UserRole
from src.discovery.schemas import (
    CrawlRunResponse,
    DiscoveryProfileCreate,
    DiscoveryProfileResponse,
    DiscoveryProfileUpdate,
    RunDiscoveryResponse,
)
from src.discovery.service import DiscoveryService
from src.users.models import User

router = APIRouter(prefix="/discovery", tags=["discovery"])

_manager_user = Depends(require_minimum_role(UserRole.MANAGER))
_sales_user = Depends(require_minimum_role(UserRole.SALES))


@router.get("/profiles", response_model=list[DiscoveryProfileResponse])
async def list_profiles(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, _sales_user],
) -> list[DiscoveryProfileResponse]:
    return await DiscoveryService(db).list_profiles(current_user)


@router.post("/profiles", response_model=DiscoveryProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    payload: DiscoveryProfileCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, _manager_user],
) -> DiscoveryProfileResponse:
    return await DiscoveryService(db).create_profile(current_user, payload)


@router.get("/profiles/{profile_id}", response_model=DiscoveryProfileResponse)
async def get_profile(
    profile_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, _sales_user],
) -> DiscoveryProfileResponse:
    return await DiscoveryService(db).get_profile(current_user, profile_id)


@router.patch("/profiles/{profile_id}", response_model=DiscoveryProfileResponse)
async def update_profile(
    profile_id: UUID,
    payload: DiscoveryProfileUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, _sales_user],
) -> DiscoveryProfileResponse:
    return await DiscoveryService(db).update_profile(current_user, profile_id, payload)


@router.delete("/profiles/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(
    profile_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, _manager_user],
) -> None:
    await DiscoveryService(db).delete_profile(current_user, profile_id)


@router.get("/profiles/{profile_id}/runs", response_model=list[CrawlRunResponse])
async def list_crawl_runs(
    profile_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, _sales_user],
) -> list[CrawlRunResponse]:
    return await DiscoveryService(db).list_runs(current_user, profile_id)


@router.post("/profiles/{profile_id}/run", response_model=RunDiscoveryResponse)
async def run_discovery(
    profile_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, _sales_user],
) -> RunDiscoveryResponse:
    return await DiscoveryService(db).trigger_run(current_user, profile_id)
