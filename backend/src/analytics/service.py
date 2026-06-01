from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.analytics.schemas import AnalyticsOverview
from src.auth.rbac import has_minimum_role
from src.common.enums import LeadStatus, UserRole
from src.leads.models import Lead
from src.users.models import User


class AnalyticsService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def _apply_access_filter(self, query, user: User):
        if has_minimum_role(user.role, UserRole.MANAGER):
            return query
        return query.where(Lead.created_by == user.id)

    async def get_overview(self, user: User) -> AnalyticsOverview:
        base_query = select(Lead)
        base_query = self._apply_access_filter(base_query, user)

        total_leads = await self.db.scalar(
            select(func.count()).select_from(base_query.subquery())
        ) or 0

        status_counts: dict[str, int] = {}
        for status in LeadStatus:
            status_query = base_query.where(Lead.status == status)
            count = await self.db.scalar(
                select(func.count()).select_from(status_query.subquery())
            ) or 0
            status_counts[status.value] = count

        contacted = status_counts.get(LeadStatus.CONTACTED.value, 0)
        replied = status_counts.get(LeadStatus.REPLIED.value, 0)
        converted = status_counts.get(LeadStatus.CONVERTED.value, 0)

        outreach_base = contacted + replied + converted
        reply_rate = round(replied / outreach_base, 4) if outreach_base else 0.0
        conversion_rate = round(converted / total_leads, 4) if total_leads else 0.0

        return AnalyticsOverview(
            total_leads=total_leads,
            total_campaigns=0,
            sent_messages=contacted + replied + converted,
            reply_rate=reply_rate,
            conversion_rate=conversion_rate,
            leads_by_status=status_counts,
        )
