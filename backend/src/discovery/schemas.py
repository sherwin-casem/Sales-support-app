import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.common.enums import CrawlRunStatus


class DiscoveryProfileBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    industries: list[str] = Field(default_factory=list)
    countries: list[str] = Field(default_factory=list)
    seed_urls: list[str] = Field(min_length=1)
    crawl_depth: int = Field(default=2, ge=1, le=5)
    max_pages: int = Field(default=50, ge=1, le=500)
    schedule_cron: str | None = Field(default=None, max_length=100)
    is_active: bool = True


class DiscoveryProfileCreate(DiscoveryProfileBase):
    pass


class DiscoveryProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    industries: list[str] | None = None
    countries: list[str] | None = None
    seed_urls: list[str] | None = None
    crawl_depth: int | None = Field(default=None, ge=1, le=5)
    max_pages: int | None = Field(default=None, ge=1, le=500)
    schedule_cron: str | None = None
    is_active: bool | None = None


class DiscoveryProfileResponse(DiscoveryProfileBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_by: uuid.UUID | None
    last_run_at: datetime | None
    created_at: datetime
    updated_at: datetime


class CrawlRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    profile_id: uuid.UUID
    status: CrawlRunStatus
    pages_crawled: int
    leads_found: int
    leads_created: int
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    celery_task_id: str | None
    created_at: datetime


class RunDiscoveryResponse(BaseModel):
    crawl_run_id: uuid.UUID
    task_id: str
    message: str = "Discovery crawl enqueued"
