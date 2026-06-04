import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.common.enums import CampaignChannel, CampaignLeadStatus, CampaignStatus, MessageChannel


class CampaignBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    channel: CampaignChannel = CampaignChannel.EMAIL


class CampaignCreate(CampaignBase):
    pass


class CampaignUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    status: CampaignStatus | None = None
    scheduled_at: datetime | None = None


class CampaignLeadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    campaign_id: uuid.UUID
    lead_id: uuid.UUID
    status: CampaignLeadStatus
    sent_at: datetime | None
    replied_at: datetime | None


class CampaignResponse(CampaignBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: CampaignStatus
    scheduled_at: datetime | None
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    lead_count: int = 0


class CampaignDetailResponse(CampaignResponse):
    campaign_leads: list[CampaignLeadResponse] = []


class AddLeadsRequest(BaseModel):
    lead_ids: list[uuid.UUID] = Field(min_length=1)


class ScheduleCampaignRequest(BaseModel):
    scheduled_at: datetime


class UpdateCampaignLeadStatusRequest(BaseModel):
    status: CampaignLeadStatus


class MessageGenerateRequest(BaseModel):
    lead_id: uuid.UUID
    channel: MessageChannel
    campaign_id: uuid.UUID | None = None
    tone: str = "professional"
    context: str | None = None


class GeneratedMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    lead_id: uuid.UUID
    campaign_id: uuid.UUID | None
    channel: MessageChannel
    subject: str | None
    body: str
    created_at: datetime
