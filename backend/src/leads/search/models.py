import uuid
from datetime import datetime

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.common.enums import CrawlRunStatus
from src.common.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class LeadSearchRun(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "lead_search_runs"

    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    seed_urls: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    parsed_criteria: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[CrawlRunStatus] = mapped_column(
        Enum(CrawlRunStatus, name="crawl_run_status", create_constraint=False, native_enum=True, create_type=False),
        nullable=False,
        default=CrawlRunStatus.PENDING,
        index=True,
    )
    preview_results: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    pages_crawled: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    celery_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
