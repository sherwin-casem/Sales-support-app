import uuid
from datetime import datetime

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.common.enums import IntentSignalType
from src.common.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class IntentSignal(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "intent_signals"

    lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    signal_type: Mapped[IntentSignalType] = mapped_column(
        Enum(IntentSignalType, name="intent_signal_type", create_constraint=False, native_enum=True, create_type=False),
        nullable=False,
        index=True,
    )
    evidence: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    detected_at: Mapped[datetime] = mapped_column(nullable=False)

    lead: Mapped["Lead"] = relationship("Lead", back_populates="intent_signals")
