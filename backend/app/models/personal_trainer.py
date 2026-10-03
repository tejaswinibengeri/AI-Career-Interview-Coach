"""
SQLAlchemy models for Personal Trainer — AI-powered Personalized Learning & Career Training System.
Supports day-by-day learning schedules, granular tasks, adaptive carry-overs, confidence ratings, and n8n webhook settings.
"""

from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base


class TrainingPlan(Base):
    """Personalized day-by-day training plan parent entity."""

    __tablename__ = "training_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    goal_dimensions: Mapped[list[str]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=list,
        nullable=False,
    )  # e.g., ["skill", "role", "company"]
    target_skill: Mapped[str | None] = mapped_column(String(150), nullable=True)
    target_role: Mapped[str | None] = mapped_column(String(150), nullable=True)
    target_company: Mapped[str | None] = mapped_column(String(150), nullable=True)
    current_skills: Mapped[list[str]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=list,
        nullable=False,
    )
    experience_level: Mapped[str] = mapped_column(String(50), default="Intermediate", nullable=False)
    daily_hours: Mapped[float] = mapped_column(Float, default=2.0, nullable=False)
    learning_preference: Mapped[str] = mapped_column(String(50), default="Balanced", nullable=False)
    target_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    estimated_duration_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    total_learning_hours: Mapped[float] = mapped_column(Float, default=60.0, nullable=False)
    overall_progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    phases_summary: Mapped[list[dict]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=list,
        nullable=False,
    )  # High-level sequence: [{"phase": 1, "title": "...", "description": "..."}]
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User")
    days: Mapped[list["TrainingDay"]] = relationship(
        "TrainingDay",
        back_populates="plan",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="TrainingDay.day_number.asc()",
    )


class TrainingDay(Base):
    """Individual training day containing specific objectives and granular tasks."""

    __tablename__ = "training_days"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plan_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("training_plans.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    day_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    phase_name: Mapped[str] = mapped_column(String(150), nullable=False)
    objective: Mapped[str] = mapped_column(String(255), nullable=False)
    topics: Mapped[list[str]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=list,
        nullable=False,
    )
    expected_outcome: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_planned_minutes: Mapped[int] = mapped_column(Integer, default=120, nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    confidence_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1 to 5
    ai_review_recommendation: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    plan: Mapped["TrainingPlan"] = relationship("TrainingPlan", back_populates="days")
    tasks: Mapped[list["TrainingTask"]] = relationship(
        "TrainingTask",
        back_populates="day",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="TrainingTask.order_index.asc()",
    )


class TrainingTask(Base):
    """Granular, minute-estimated task within a training day."""

    __tablename__ = "training_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    day_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("training_days.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    task_type: Mapped[str] = mapped_column(
        String(50), default="practice", nullable=False
    )  # "theory", "practice", "project", "assessment"
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="not_started", nullable=False
    )  # "not_started", "in_progress", "completed", "skipped", "rescheduled"
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_carried_over: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    original_day_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    time_spent_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationship
    day: Mapped["TrainingDay"] = relationship("TrainingDay", back_populates="tasks")


class PersonalTrainerSettings(Base):
    """User-specific notification settings and n8n webhook preferences."""

    __tablename__ = "personal_trainer_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    preferred_time: Mapped[str] = mapped_column(String(20), default="09:00", nullable=False)
    notification_channel: Mapped[str] = mapped_column(String(50), default="email", nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationship
    user: Mapped["User"] = relationship("User")
