import uuid

from pydantic import BaseModel


class AnalyticsOverview(BaseModel):
    total_leads: int
    total_campaigns: int
    sent_messages: int
    reply_rate: float
    conversion_rate: float
    leads_by_status: dict[str, int]


class CampaignAnalytics(BaseModel):
    campaign_id: uuid.UUID
    campaign_name: str
    total_leads: int
    sent: int
    replied: int
    failed: int
    pending: int
    reply_rate: float
