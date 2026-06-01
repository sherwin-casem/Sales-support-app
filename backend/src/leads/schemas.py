import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.common.enums import LeadStatus


class LeadBase(BaseModel):
    company_name: str = Field(min_length=1, max_length=255)
    website: str | None = Field(default=None, max_length=512)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    industry: str | None = Field(default=None, max_length=255)
    employee_count: int | None = Field(default=None, ge=0)
    revenue: Decimal | None = Field(default=None, ge=0)
    country: str | None = Field(default=None, max_length=100)
    status: LeadStatus = LeadStatus.NEW


class LeadCreate(LeadBase):
    pass


class LeadUpdate(BaseModel):
    company_name: str | None = Field(default=None, min_length=1, max_length=255)
    website: str | None = Field(default=None, max_length=512)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    industry: str | None = Field(default=None, max_length=255)
    employee_count: int | None = Field(default=None, ge=0)
    revenue: Decimal | None = Field(default=None, ge=0)
    country: str | None = Field(default=None, max_length=100)
    status: LeadStatus | None = None


class DecisionMakerBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    role: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = None
    linkedin: str | None = Field(default=None, max_length=512)


class DecisionMakerCreate(DecisionMakerBase):
    pass


class DecisionMakerResponse(DecisionMakerBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    lead_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class LeadResponse(LeadBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class LeadDetailResponse(LeadResponse):
    decision_makers: list[DecisionMakerResponse] = []


class LeadImportResult(BaseModel):
    created: int
    failed: int
    errors: list[str] = []
