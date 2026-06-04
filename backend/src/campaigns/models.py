import uuid
from datetime import datetime

from sqlalchemy import Boolean, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.common.enums import CampaignChannel, CampaignLeadStatus, CampaignStatus, MessageChannel
from src.common.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Campaign(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "campaigns"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[CampaignStatus] = mapped_column(
        Enum(CampaignStatus, name="campaign_status", create_constraint=False, native_enum=True, create_type=False),
        nullable=False,
        default=CampaignStatus.DRAFT,
        index=True,
    )
    channel: Mapped[CampaignChannel] = mapped_column(
        Enum(CampaignChannel, name="campaign_channel", create_constraint=False, native_enum=True, create_type=False),
        nullable=False,
        default=CampaignChannel.EMAIL,
    )
    scheduled_at: Mapped[datetime | None] = mapped_column(nullable=True, index=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    campaign_leads: Mapped[list["CampaignLead"]] = relationship(
        "CampaignLead",
        back_populates="campaign",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class CampaignLead(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "campaign_leads"

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[CampaignLeadStatus] = mapped_column(
        Enum(
            CampaignLeadStatus,
            name="campaign_lead_status",
            create_constraint=False,
            native_enum=True,
            create_type=False,
        ),
        nullable=False,
        default=CampaignLeadStatus.PENDING,
        index=True,
    )
    sent_at: Mapped[datetime | None] = mapped_column(nullable=True)
    replied_at: Mapped[datetime | None] = mapped_column(nullable=True)

    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="campaign_leads")
    messages: Mapped[list["CampaignMessage"]] = relationship(
        "CampaignMessage",
        back_populates="campaign_lead",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class CampaignMessage(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "campaign_messages"

    campaign_lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("campaign_leads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subject: Mapped[str | None] = mapped_column(String(512), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    generated_by_ai: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    campaign_lead: Mapped["CampaignLead"] = relationship("CampaignLead", back_populates="messages")


class GeneratedMessage(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "generated_messages"

    lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    channel: Mapped[MessageChannel] = mapped_column(
        Enum(MessageChannel, name="message_channel", create_constraint=False, native_enum=True, create_type=False),
        nullable=False,
        index=True,
    )
    subject: Mapped[str | None] = mapped_column(String(512), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
