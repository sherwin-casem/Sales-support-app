from pydantic import BaseModel


class AnalyticsOverview(BaseModel):
    total_leads: int
    total_campaigns: int
    sent_messages: int
    reply_rate: float
    conversion_rate: float
    leads_by_status: dict[str, int]
