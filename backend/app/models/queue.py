from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.time_utils import ist_now_naive


class Service(Base):
    __tablename__ = "services"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255))
    avg_service_minutes: Mapped[float] = mapped_column(Float, default=5.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=ist_now_naive
    )

    counters: Mapped[list["Counter"]] = relationship(
        back_populates="service"
    )
    tokens: Mapped[list["QueueToken"]] = relationship(
        back_populates="service"
    )

    __table_args__ = (
        CheckConstraint("avg_service_minutes > 0"),
    )


class Counter(Base):
    __tablename__ = "counters"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    service_id: Mapped[int] = mapped_column(
        ForeignKey("services.id"), nullable=False
    )
    counter_number: Mapped[int] = mapped_column(Integer, nullable=False)
    label: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="closed", nullable=False
    )

    service: Mapped["Service"] = relationship(back_populates="counters")
    tokens: Mapped[list["QueueToken"]] = relationship(
        back_populates="counter"
    )

    __table_args__ = (
        CheckConstraint("counter_number > 0"),
        UniqueConstraint(
            "service_id",
            "counter_number",
            name="uq_counters_service_counter_number",
        ),
    )


class QueueToken(Base):
    __tablename__ = "queue_tokens"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    token_number: Mapped[str] = mapped_column(
        String(30), unique=True, nullable=False, index=True
    )
    service_id: Mapped[int] = mapped_column(
        ForeignKey("services.id"), nullable=False
    )
    counter_id: Mapped[int | None] = mapped_column(
        ForeignKey("counters.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(20), default="waiting", nullable=False
    )
    estimated_wait_minutes: Mapped[float | None] = mapped_column(Float)
    issued_at: Mapped[datetime] = mapped_column(
        DateTime, default=ist_now_naive
    )
    called_at: Mapped[datetime | None] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    qr_token_hash: Mapped[str | None] = mapped_column(
        String(64), unique=True, nullable=True
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime)
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime)
    verification_code: Mapped[str | None] = mapped_column(String(6), unique=True, nullable=True)

    service: Mapped["Service"] = relationship(back_populates="tokens")
    counter: Mapped["Counter | None"] = relationship(
        back_populates="tokens"
    )
    service_record: Mapped["ServiceRecord | None"] = relationship(
        back_populates="token", uselist=False
    )


class ServiceRecord(Base):
    __tablename__ = "service_records"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    token_id: Mapped[int] = mapped_column(
        ForeignKey("queue_tokens.id"), unique=True, nullable=False
    )
    counter_id: Mapped[int] = mapped_column(
        ForeignKey("counters.id"), nullable=False
    )
    waiting_time_minutes: Mapped[float] = mapped_column(Float, default=0.0)
    service_time_minutes: Mapped[float] = mapped_column(Float, default=0.0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime)

    token: Mapped["QueueToken"] = relationship(
        back_populates="service_record"
    )

