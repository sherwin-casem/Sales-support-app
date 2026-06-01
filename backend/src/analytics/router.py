from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.analytics.schemas import AnalyticsOverview
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
