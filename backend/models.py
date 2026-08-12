"""SQLAlchemy table models for operational and closed-loop data."""

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Shipment(Base):
    __tablename__ = "shipments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    shipment_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    country: Mapped[str] = mapped_column(String(100))
    vendor: Mapped[str] = mapped_column(String(255))
    product_group: Mapped[str] = mapped_column(String(100))
    shipment_mode: Mapped[str] = mapped_column(String(100))
    line_item_quantity: Mapped[float] = mapped_column(Float)
    line_item_value: Mapped[float] = mapped_column(Float)
    weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    freight_cost: Mapped[float | None] = mapped_column(Float, nullable=True)
    scheduled_delivery_date: Mapped[date] = mapped_column(Date)
    available_budget: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Decision(Base):
    __tablename__ = "decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    shipment_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("shipments.shipment_id"), index=True
    )
    selected_option: Mapped[str] = mapped_column(String(1))
    option_title: Mapped[str] = mapped_column(String(100))
    predicted_delay_probability: Mapped[float] = mapped_column(Float)
    predicted_delay_days: Mapped[float] = mapped_column(Float)
    predicted_cost: Mapped[float] = mapped_column(Float)
    available_budget: Mapped[float] = mapped_column(Float)
    decision_status: Mapped[str] = mapped_column(String(20), default="EXECUTED")
    executed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    outcomes: Mapped[list["Outcome"]] = relationship(back_populates="decision")
    feedback: Mapped[list["ModelFeedback"]] = relationship(back_populates="decision")


class Outcome(Base):
    __tablename__ = "outcomes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    decision_id: Mapped[int] = mapped_column(ForeignKey("decisions.id"), index=True)
    actual_cost: Mapped[float] = mapped_column(Float)
    actual_delay_days: Mapped[float] = mapped_column(Float)
    success: Mapped[bool] = mapped_column(Boolean)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    decision: Mapped[Decision] = relationship(back_populates="outcomes")


class ModelFeedback(Base):
    __tablename__ = "model_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    decision_id: Mapped[int] = mapped_column(ForeignKey("decisions.id"), index=True)
    predicted_cost: Mapped[float] = mapped_column(Float)
    actual_cost: Mapped[float] = mapped_column(Float)
    cost_error: Mapped[float] = mapped_column(Float)
    predicted_delay_days: Mapped[float] = mapped_column(Float)
    actual_delay_days: Mapped[float] = mapped_column(Float)
    delay_error: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    decision: Mapped[Decision] = relationship(back_populates="feedback")
