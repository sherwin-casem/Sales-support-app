import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.common.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class EnrichmentRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "enrichment_records"

    lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    raw_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    domain: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    scraped_title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    scraped_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    inferred_industry: Mapped[str | None] = mapped_column(String(255), nullable=True)
    inferred_employee_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    enriched_at: Mapped[datetime] = mapped_column(nullable=False)
