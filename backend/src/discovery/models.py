import uuid
from datetime import datetime

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.common.enums import CrawlRunStatus
from src.common.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class DiscoveryProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "discovery_profiles"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    industries: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    countries: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    seed_urls: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    crawl_depth: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    max_pages: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    schedule_cron: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    last_run_at: Mapped[datetime | None] = mapped_column(nullable=True)

    crawl_runs: Mapped[list["CrawlRun"]] = relationship(
        "CrawlRun",
        back_populates="profile",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class CrawlRun(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "crawl_runs"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("discovery_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[CrawlRunStatus] = mapped_column(
        Enum(CrawlRunStatus, name="crawl_run_status", create_constraint=False, native_enum=True, create_type=False),
        nullable=False,
        default=CrawlRunStatus.PENDING,
        index=True,
    )
    pages_crawled: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    leads_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    leads_created: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    celery_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    profile: Mapped["DiscoveryProfile"] = relationship("DiscoveryProfile", back_populates="crawl_runs")
