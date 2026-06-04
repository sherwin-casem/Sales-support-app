from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import require_minimum_role
from src.campaigns.schemas import (
    AddLeadsRequest,
    CampaignCreate,
    CampaignDetailResponse,
    CampaignLeadResponse,
    CampaignResponse,
    CampaignUpdate,
    GeneratedMessageResponse,
    MessageGenerateRequest,
    ScheduleCampaignRequest,
    UpdateCampaignLeadStatusRequest,
)
from src.campaigns.service import CampaignService, MessageService
from src.common.database import get_db
from src.common.enums import UserRole
from src.users.models import User

router = APIRouter(prefix="/campaigns", tags=["campaigns"])
messages_router = APIRouter(prefix="/messages", tags=["messages"])


@router.get("", response_model=list[CampaignResponse])
async def list_campaigns(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_minimum_role(UserRole.SALES))],
) -> list[CampaignResponse]:
    return await CampaignService(db).list_campaigns(current_user)


@router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    payload: CampaignCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_minimum_role(UserRole.SALES))],
) -> CampaignResponse:
    return await CampaignService(db).create_campaign(current_user, payload)


@router.get("/{campaign_id}", response_model=CampaignDetailResponse)
async def get_campaign(
    campaign_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_minimum_role(UserRole.SALES))],
) -> CampaignDetailResponse:
    return await CampaignService(db).get_campaign(current_user, campaign_id)


@router.patch("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: UUID,
    payload: CampaignUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_minimum_role(UserRole.SALES))],
) -> CampaignResponse:
    return await CampaignService(db).update_campaign(current_user, campaign_id, payload)


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(
    campaign_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_minimum_role(UserRole.MANAGER))],
) -> None:
    await CampaignService(db).delete_campaign(current_user, campaign_id)


@router.post("/{campaign_id}/leads", response_model=CampaignDetailResponse)
async def add_campaign_leads(
    campaign_id: UUID,
    payload: AddLeadsRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_minimum_role(UserRole.SALES))],
) -> CampaignDetailResponse:
    return await CampaignService(db).add_leads(current_user, campaign_id, payload)


@router.delete("/{campaign_id}/leads/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_campaign_lead(
    campaign_id: UUID,
    lead_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_minimum_role(UserRole.SALES))],
) -> None:
    await CampaignService(db).remove_lead(current_user, campaign_id, lead_id)


@router.post("/{campaign_id}/schedule", response_model=CampaignResponse)
async def schedule_campaign(
    campaign_id: UUID,
    payload: ScheduleCampaignRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_minimum_role(UserRole.SALES))],
) -> CampaignResponse:
    return await CampaignService(db).schedule(current_user, campaign_id, payload.scheduled_at)


@router.post("/{campaign_id}/send")
async def send_campaign(
    campaign_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_minimum_role(UserRole.MANAGER))],
) -> dict:
    return await CampaignService(db).send_now(current_user, campaign_id)


@router.patch("/{campaign_id}/leads/{lead_id}/status", response_model=CampaignLeadResponse)
async def update_campaign_lead_status(
    campaign_id: UUID,
    lead_id: UUID,
    payload: UpdateCampaignLeadStatusRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_minimum_role(UserRole.SALES))],
) -> CampaignLeadResponse:
    return await CampaignService(db).update_lead_status(current_user, campaign_id, lead_id, payload)


@messages_router.post("/generate", response_model=GeneratedMessageResponse, status_code=status.HTTP_201_CREATED)
async def generate_message(
    payload: MessageGenerateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_minimum_role(UserRole.SALES))],
) -> GeneratedMessageResponse:
    return await MessageService(db).generate(current_user, payload)


@messages_router.get("", response_model=list[GeneratedMessageResponse])
async def list_messages(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_minimum_role(UserRole.SALES))],
    lead_id: UUID | None = None,
    campaign_id: UUID | None = None,
) -> list[GeneratedMessageResponse]:
    return await MessageService(db).list_messages(current_user, lead_id=lead_id, campaign_id=campaign_id)


@messages_router.get("/{message_id}", response_model=GeneratedMessageResponse)
async def get_message(
    message_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_minimum_role(UserRole.SALES))],
) -> GeneratedMessageResponse:
    return await MessageService(db).get_message(current_user, message_id)
