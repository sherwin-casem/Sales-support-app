import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.common.enums import (
    CrawlRunStatus,
    EmailVerificationStatus,
    LeadSource,
    LeadStatus,
    PhoneVerificationStatus,
)
from src.common.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Lead(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "leads"

    company_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    website: Mapped[str | None] = mapped_column(String(512), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    employee_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    revenue: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    status: Mapped[LeadStatus] = mapped_column(
        Enum(LeadStatus, name="lead_status", create_constraint=False, native_enum=True, create_type=False),
        nullable=False,
        default=LeadStatus.NEW,
        index=True,
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source: Mapped[LeadSource] = mapped_column(
        Enum(LeadSource, name="lead_source", create_constraint=False, native_enum=True, create_type=False),
        nullable=False,
        default=LeadSource.MANUAL,
        index=True,
    )
    domain_normalized: Mapped[str | None] = mapped_column(String(512), nullable=True, index=True)
    discovery_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("discovery_profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    email_verification_status: Mapped[EmailVerificationStatus] = mapped_column(
        Enum(
            EmailVerificationStatus,
            name="email_verification_status",
            create_constraint=False,
            native_enum=True,
            create_type=False,
        ),
        nullable=False,
        default=EmailVerificationStatus.UNKNOWN,
    )
    phone_verification_status: Mapped[PhoneVerificationStatus] = mapped_column(
        Enum(
            PhoneVerificationStatus,
            name="phone_verification_status",
            create_constraint=False,
            native_enum=True,
            create_type=False,
        ),
        nullable=False,
        default=PhoneVerificationStatus.UNKNOWN,
    )
    email_verified_at: Mapped[datetime | None] = mapped_column(nullable=True)
    intent_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)
    duplicate_of_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("leads.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_duplicate: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)

    decision_makers: Mapped[list["DecisionMaker"]] = relationship(
        "DecisionMaker",
        back_populates="lead",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    intent_signals: Mapped[list["IntentSignal"]] = relationship(
        "IntentSignal",
        back_populates="lead",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

class DecisionMaker(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "decision_makers"

    lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    linkedin: Mapped[str | None] = mapped_column(String(512), nullable=True)
    email_verification_status: Mapped[EmailVerificationStatus] = mapped_column(
        Enum(
            EmailVerificationStatus,
            name="email_verification_status",
            create_constraint=False,
            native_enum=True,
            create_type=False,
        ),
        nullable=False,
        default=EmailVerificationStatus.UNKNOWN,
    )

    lead: Mapped["Lead"] = relationship("Lead", back_populates="decision_makers")
