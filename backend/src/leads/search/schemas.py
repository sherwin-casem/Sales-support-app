import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LeadSearchCriteria(BaseModel):
    industries: list[str] = Field(default_factory=list)
    countries: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    company_signals: list[str] = Field(default_factory=list)
    exclude_keywords: list[str] = Field(default_factory=list)
    relevance_notes: str = ""


class LeadPreviewItem(BaseModel):
    company_name: str
    website: str | None = None
    email: str | None = None
    phone: str | None = None
    country: str | None = None
    industry: str | None = None
    match_score: int = Field(ge=0, le=100)
    match_reason: str = ""
    scraped_title: str | None = None
    already_in_pipeline: bool = False


class LeadSearchRequest(BaseModel):
    query: str = Field(min_length=3, max_length=2000)
    max_results: int = Field(default=20, ge=5, le=50)


class LeadSearchStartResponse(BaseModel):
    search_id: uuid.UUID
    task_id: str
    message: str = "Lead search enqueued"


class LeadSearchRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    query_text: str
    seed_urls: list[str]
    parsed_criteria: dict
    status: str
    preview_items: list[LeadPreviewItem]
    pages_crawled: int
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


class LeadSearchSaveItem(BaseModel):
    company_name: str = Field(min_length=1, max_length=255)
    website: str | None = None
    email: str | None = None
    phone: str | None = None
    country: str | None = None
    industry: str | None = None


class LeadSearchSaveRequest(BaseModel):
    items: list[LeadSearchSaveItem] = Field(min_length=1)


class LeadSearchSaveResponse(BaseModel):
    created: int
    skipped: int
    lead_ids: list[uuid.UUID]
