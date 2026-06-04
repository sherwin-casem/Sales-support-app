"""SMTP email sender for campaigns."""

from __future__ import annotations

import smtplib
import uuid
from datetime import UTC, datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.campaigns.models import CampaignLead, CampaignMessage
from src.common.config import get_settings
from src.common.enums import CampaignLeadStatus, CampaignStatus
from src.common.sync_database import get_sync_db
from src.leads.models import Lead


def send_campaign_lead_email(campaign_lead_id: uuid.UUID) -> dict:
    settings = get_settings()

    with get_sync_db() as session:
        campaign_lead = session.scalar(
            select(CampaignLead)
            .where(CampaignLead.id == campaign_lead_id)
            .options(
                selectinload(CampaignLead.campaign),
                selectinload(CampaignLead.messages),
            )
        )
        if campaign_lead is None:
            return {"error": "campaign_lead_not_found"}

        if campaign_lead.status == CampaignLeadStatus.SENT:
            return {"skipped": True, "reason": "already_sent"}

        lead = session.get(Lead, campaign_lead.lead_id)
        if lead is None or not lead.email:
            campaign_lead.status = CampaignLeadStatus.FAILED
            return {"error": "lead_missing_email"}

        message = campaign_lead.messages[0] if campaign_lead.messages else None
        if message is None:
            campaign_lead.status = CampaignLeadStatus.FAILED
            return {"error": "no_message"}

        if settings.smtp_dry_run or not settings.smtp_host:
            campaign_lead.status = CampaignLeadStatus.SENT
            campaign_lead.sent_at = datetime.now(UTC)
            campaign = campaign_lead.campaign
            if campaign and campaign.status == CampaignStatus.SCHEDULED:
                campaign.status = CampaignStatus.RUNNING
            return {"dry_run": True, "to": lead.email}

        try:
            msg = MIMEMultipart()
            msg["From"] = settings.smtp_from_email
            msg["To"] = lead.email
            msg["Subject"] = message.subject or f"Hello from Parijat"
            msg.attach(MIMEText(message.body, "plain"))

            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
                if settings.smtp_use_tls:
                    server.starttls()
                if settings.smtp_user and settings.smtp_password:
                    server.login(settings.smtp_user, settings.smtp_password)
                server.sendmail(settings.smtp_from_email, [lead.email], msg.as_string())

            campaign_lead.status = CampaignLeadStatus.SENT
            campaign_lead.sent_at = datetime.now(UTC)
            campaign = campaign_lead.campaign
            if campaign:
                campaign.status = CampaignStatus.RUNNING
            return {"sent": True, "to": lead.email}
        except Exception as exc:
            campaign_lead.status = CampaignLeadStatus.FAILED
            return {"error": str(exc)}
