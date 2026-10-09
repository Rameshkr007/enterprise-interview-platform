from __future__ import annotations

import enum
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import JSON, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SubscriptionStatus(str, enum.Enum):
    active = "active"
    trialing = "trialing"
    past_due = "past_due"
    canceled = "canceled"
    expired = "expired"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    plan_id: Mapped[str] = mapped_column(String(50), nullable=False, default="starter")
    tier: Mapped[str] = mapped_column(String(50), nullable=False, default="Starter")
    billing_cycle: Mapped[str] = mapped_column(String(20), nullable=False, default="yearly")
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus, name="subscription_status", native_enum=False),
        nullable=False,
        default=SubscriptionStatus.active,
    )
    amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    credits_total: Mapped[int] = mapped_column(Integer, nullable=False, default=1000)
    credits_remaining: Mapped[int] = mapped_column(Integer, nullable=False, default=1000)
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    razorpay_order_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    current_period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    current_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    transactions: Mapped[list["PaymentTransaction"]] = relationship(
        back_populates="subscription", lazy="noload", cascade="all, delete-orphan"
    )


class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subscription_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    session_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    payment_gateway: Mapped[str] = mapped_column(String(50), nullable=False, default="stripe")
    gateway_payment_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="USD")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False, default="card")
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    subscription: Mapped["Subscription | None"] = relationship(back_populates="transactions", lazy="noload")
