import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field


class EnrichmentPreviewRequest(BaseModel):
    website: str | None = None
    company_name: str = Field(min_length=1, max_length=255)


class EnrichmentRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    lead_id: uuid.UUID
    source: str
    domain: str | None
    scraped_title: str | None
    scraped_description: str | None
    inferred_industry: str | None
    inferred_employee_count: int | None
    enriched_at: datetime
    created_at: datetime


class EnrichmentJobResponse(BaseModel):
    task_id: str
    message: str = "Enrichment job enqueued"


class EnrichmentPreviewResponse(BaseModel):
    company_name: str
    domain: str | None
    scraped_title: str | None
    scraped_description: str | None
    inferred_industry: str | None
    decision_makers_found: int = 0
