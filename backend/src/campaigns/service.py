from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.ai.openai_client import generate_outreach_message
from src.auth.rbac import has_minimum_role
from src.campaigns.models import Campaign, CampaignLead, CampaignMessage, GeneratedMessage
from src.campaigns.schemas import (
    AddLeadsRequest,
    CampaignCreate,
    CampaignDetailResponse,
    CampaignLeadResponse,
    CampaignResponse,
    CampaignUpdate,
    GeneratedMessageResponse,
    MessageGenerateRequest,
    UpdateCampaignLeadStatusRequest,
)
from src.common.enums import CampaignLeadStatus, CampaignStatus, MessageChannel, UserRole
from src.common.exceptions import ForbiddenException, NotFoundException
from src.leads.models import Lead
from src.users.models import User


class CampaignService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    def _access_filter(self, query, user: User):
        if has_minimum_role(user.role, UserRole.MANAGER):
            return query
        return query.where(Campaign.created_by == user.id)

    async def _get_campaign(self, user: User, campaign_id: uuid.UUID) -> Campaign:
        query = (
            select(Campaign)
            .where(Campaign.id == campaign_id)
            .options(selectinload(Campaign.campaign_leads))
        )
        query = self._access_filter(query, user)
        campaign = await self.db.scalar(query)
        if campaign is None:
            raise NotFoundException("Campaign not found", code="CAMPAIGN_NOT_FOUND")
        return campaign

    async def list_campaigns(self, user: User) -> list[CampaignResponse]:
        query = self._access_filter(select(Campaign), user).order_by(Campaign.created_at.desc())
        campaigns = (await self.db.scalars(query)).all()
        result = []
        for c in campaigns:
            resp = CampaignResponse.model_validate(c)
            resp.lead_count = len(c.campaign_leads)
            result.append(resp)
        return result

    async def get_campaign(self, user: User, campaign_id: uuid.UUID) -> CampaignDetailResponse:
        campaign = await self._get_campaign(user, campaign_id)
        resp = CampaignDetailResponse.model_validate(campaign)
        resp.lead_count = len(campaign.campaign_leads)
        resp.campaign_leads = [CampaignLeadResponse.model_validate(cl) for cl in campaign.campaign_leads]
        return resp

    async def create_campaign(self, user: User, payload: CampaignCreate) -> CampaignResponse:
        campaign = Campaign(**payload.model_dump(), created_by=user.id)
        self.db.add(campaign)
        await self.db.flush()
        await self.db.refresh(campaign)
        resp = CampaignResponse.model_validate(campaign)
        resp.lead_count = 0
        return resp

    async def update_campaign(
        self, user: User, campaign_id: uuid.UUID, payload: CampaignUpdate
    ) -> CampaignResponse:
        campaign = await self._get_campaign(user, campaign_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(campaign, field, value)
        await self.db.flush()
        await self.db.refresh(campaign)
        resp = CampaignResponse.model_validate(campaign)
        resp.lead_count = len(campaign.campaign_leads)
        return resp

    async def delete_campaign(self, user: User, campaign_id: uuid.UUID) -> None:
        if not has_minimum_role(user.role, UserRole.MANAGER):
            raise ForbiddenException("Only managers can delete campaigns", code="INSUFFICIENT_ROLE")
        campaign = await self._get_campaign(user, campaign_id)
        await self.db.delete(campaign)

    async def add_leads(self, user: User, campaign_id: uuid.UUID, payload: AddLeadsRequest) -> CampaignDetailResponse:
        campaign = await self._get_campaign(user, campaign_id)
        existing = {cl.lead_id for cl in campaign.campaign_leads}
        for lead_id in payload.lead_ids:
            if lead_id in existing:
                continue
            campaign.campaign_leads.append(CampaignLead(campaign_id=campaign.id, lead_id=lead_id))
        await self.db.flush()
        return await self.get_campaign(user, campaign_id)

    async def remove_lead(self, user: User, campaign_id: uuid.UUID, lead_id: uuid.UUID) -> None:
        campaign = await self._get_campaign(user, campaign_id)
        for cl in list(campaign.campaign_leads):
            if cl.lead_id == lead_id:
                await self.db.delete(cl)
                return
        raise NotFoundException("Lead not in campaign", code="LEAD_NOT_IN_CAMPAIGN")

    async def schedule(self, user: User, campaign_id: uuid.UUID, scheduled_at: datetime) -> CampaignResponse:
        campaign = await self._get_campaign(user, campaign_id)
        campaign.scheduled_at = scheduled_at
        campaign.status = CampaignStatus.SCHEDULED
        await self.db.flush()
        resp = CampaignResponse.model_validate(campaign)
        resp.lead_count = len(campaign.campaign_leads)
        return resp

    async def send_now(self, user: User, campaign_id: uuid.UUID) -> dict:
        if not has_minimum_role(user.role, UserRole.MANAGER):
            raise ForbiddenException("Only managers can trigger send", code="INSUFFICIENT_ROLE")
        campaign = await self._get_campaign(user, campaign_id)
        campaign.status = CampaignStatus.RUNNING
        from src.jobs.tasks import send_campaign_email_task

        task_ids = []
        for cl in campaign.campaign_leads:
            if cl.status == CampaignLeadStatus.PENDING:
                if not cl.messages:
                    lead = await self.db.get(Lead, cl.lead_id)
                    if lead:
                        subject, body = generate_outreach_message(
                            channel=campaign.channel.value,
                            company_name=lead.company_name,
                            contact_name=None,
                            contact_role=None,
                            industry=lead.industry,
                        )
                        self.db.add(
                            CampaignMessage(
                                campaign_lead_id=cl.id,
                                subject=subject,
                                body=body,
                                generated_by_ai=True,
                            )
                        )
                task = send_campaign_email_task.delay(str(cl.id))
                task_ids.append(task.id)
        await self.db.flush()
        return {"enqueued": len(task_ids), "task_ids": task_ids}

    async def update_lead_status(
        self,
        user: User,
        campaign_id: uuid.UUID,
        lead_id: uuid.UUID,
        payload: UpdateCampaignLeadStatusRequest,
    ) -> CampaignLeadResponse:
        campaign = await self._get_campaign(user, campaign_id)
        for cl in campaign.campaign_leads:
            if cl.lead_id == lead_id:
                cl.status = payload.status
                if payload.status == CampaignLeadStatus.REPLIED:
                    cl.replied_at = datetime.now(UTC)
                await self.db.flush()
                await self.db.refresh(cl)
                return CampaignLeadResponse.model_validate(cl)
        raise NotFoundException("Lead not in campaign", code="LEAD_NOT_IN_CAMPAIGN")


class MessageService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def generate(self, user: User, payload: MessageGenerateRequest) -> GeneratedMessageResponse:
        lead = await self.db.get(Lead, payload.lead_id)
        if lead is None:
            raise NotFoundException("Lead not found", code="LEAD_NOT_FOUND")
        if not has_minimum_role(user.role, UserRole.MANAGER) and lead.created_by != user.id:
            raise ForbiddenException("Cannot access lead", code="FORBIDDEN")

        dm = lead.decision_makers[0] if lead.decision_makers else None
        subject, body = generate_outreach_message(
            channel=payload.channel.value,
            company_name=lead.company_name,
            contact_name=dm.name if dm else None,
            contact_role=dm.role if dm else None,
            industry=lead.industry,
            tone=payload.tone,
            extra_context=payload.context,
        )
        record = GeneratedMessage(
            lead_id=lead.id,
            campaign_id=payload.campaign_id,
            channel=MessageChannel(payload.channel.value),
            subject=subject,
            body=body,
            created_by=user.id,
        )
        self.db.add(record)
        await self.db.flush()
        await self.db.refresh(record)
        return GeneratedMessageResponse.model_validate(record)

    async def list_messages(
        self,
        user: User,
        *,
        lead_id: uuid.UUID | None = None,
        campaign_id: uuid.UUID | None = None,
    ) -> list[GeneratedMessageResponse]:
        query = select(GeneratedMessage).order_by(GeneratedMessage.created_at.desc())
        if lead_id:
            query = query.where(GeneratedMessage.lead_id == lead_id)
        if campaign_id:
            query = query.where(GeneratedMessage.campaign_id == campaign_id)
        if not has_minimum_role(user.role, UserRole.MANAGER):
            query = query.where(GeneratedMessage.created_by == user.id)
        records = (await self.db.scalars(query.limit(100))).all()
        return [GeneratedMessageResponse.model_validate(r) for r in records]

    async def get_message(self, user: User, message_id: uuid.UUID) -> GeneratedMessageResponse:
        record = await self.db.get(GeneratedMessage, message_id)
        if record is None:
            raise NotFoundException("Message not found", code="MESSAGE_NOT_FOUND")
        if not has_minimum_role(user.role, UserRole.MANAGER) and record.created_by != user.id:
            raise ForbiddenException("Cannot access message", code="FORBIDDEN")
        return GeneratedMessageResponse.model_validate(record)
