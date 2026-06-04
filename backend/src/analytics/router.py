from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.analytics.schemas import AnalyticsOverview, CampaignAnalytics
from src.analytics.service import AnalyticsService
from src.auth.dependencies import require_minimum_role
from src.common.database import get_db
from src.common.enums import UserRole
from src.users.models import User

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=AnalyticsOverview)
async def get_analytics_overview(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_minimum_role(UserRole.SALES))],
) -> AnalyticsOverview:
    service = AnalyticsService(db)
    return await service.get_overview(current_user)


@router.get("/campaigns/{campaign_id}", response_model=CampaignAnalytics)
async def get_campaign_analytics(
    campaign_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(require_minimum_role(UserRole.SALES))],
) -> CampaignAnalytics:
    return await AnalyticsService(db).get_campaign_analytics(current_user, campaign_id)
