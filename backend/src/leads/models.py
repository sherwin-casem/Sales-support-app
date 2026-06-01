import uuid
from decimal import Decimal

from sqlalchemy import Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.common.enums import LeadStatus
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

    decision_makers: Mapped[list["DecisionMaker"]] = relationship(
        "DecisionMaker",
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

    lead: Mapped["Lead"] = relationship("Lead", back_populates="decision_makers")
