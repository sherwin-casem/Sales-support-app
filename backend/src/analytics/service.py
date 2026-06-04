from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.analytics.schemas import AnalyticsOverview, CampaignAnalytics
from src.auth.rbac import has_minimum_role
from src.campaigns.models import Campaign, CampaignLead
from src.common.enums import CampaignLeadStatus, LeadStatus, UserRole
from src.leads.models import Lead
from src.users.models import User


class AnalyticsService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def _apply_access_filter(self, query, user: User):
        if has_minimum_role(user.role, UserRole.MANAGER):
            return query
        return query.where(Lead.created_by == user.id)

    def _campaign_access_filter(self, query, user: User):
        if has_minimum_role(user.role, UserRole.MANAGER):
            return query
        return query.where(Campaign.created_by == user.id)

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

        campaign_query = self._campaign_access_filter(select(Campaign), user)
        total_campaigns = await self.db.scalar(
            select(func.count()).select_from(campaign_query.subquery())
        ) or 0

        cl_query = select(CampaignLead).join(Campaign, CampaignLead.campaign_id == Campaign.id)
        if not has_minimum_role(user.role, UserRole.MANAGER):
            cl_query = cl_query.where(Campaign.created_by == user.id)

        sent = await self.db.scalar(
            select(func.count()).select_from(
                cl_query.where(CampaignLead.status == CampaignLeadStatus.SENT).subquery()
            )
        ) or 0
        replied = await self.db.scalar(
            select(func.count()).select_from(
                cl_query.where(CampaignLead.status == CampaignLeadStatus.REPLIED).subquery()
            )
        ) or 0
        converted_leads = status_counts.get(LeadStatus.CONVERTED.value, 0)

        reply_rate = round(replied / sent, 4) if sent else 0.0
        conversion_rate = round(converted_leads / total_leads, 4) if total_leads else 0.0

        return AnalyticsOverview(
            total_leads=total_leads,
            total_campaigns=total_campaigns,
            sent_messages=sent,
            reply_rate=reply_rate,
            conversion_rate=conversion_rate,
            leads_by_status=status_counts,
        )

    async def get_campaign_analytics(self, user: User, campaign_id) -> CampaignAnalytics:
        from uuid import UUID

        from src.common.exceptions import NotFoundException

        cid = campaign_id if isinstance(campaign_id, UUID) else UUID(str(campaign_id))
        query = select(Campaign).where(Campaign.id == cid)
        query = self._campaign_access_filter(query, user)
        campaign = await self.db.scalar(query)
        if campaign is None:
            raise NotFoundException("Campaign not found", code="CAMPAIGN_NOT_FOUND")

        leads = (
            await self.db.scalars(select(CampaignLead).where(CampaignLead.campaign_id == cid))
        ).all()
        total = len(leads)
        sent = sum(1 for cl in leads if cl.status == CampaignLeadStatus.SENT)
        replied = sum(1 for cl in leads if cl.status == CampaignLeadStatus.REPLIED)
        failed = sum(1 for cl in leads if cl.status == CampaignLeadStatus.FAILED)
        pending = sum(1 for cl in leads if cl.status == CampaignLeadStatus.PENDING)

        return CampaignAnalytics(
            campaign_id=cid,
            campaign_name=campaign.name,
            total_leads=total,
            sent=sent,
            replied=replied,
            failed=failed,
            pending=pending,
            reply_rate=round(replied / sent, 4) if sent else 0.0,
        )
