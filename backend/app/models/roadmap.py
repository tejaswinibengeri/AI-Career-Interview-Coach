"""
SQLAlchemy models for Personalized Career Roadmaps, Roadmap Items, and Completion Progress.
"""

from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base


class Roadmap(Base):
    """Personalized Career Roadmap parent entity."""

    __tablename__ = "roadmaps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    occupation_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("occupations.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    target_role: Mapped[str] = mapped_column(String(255), nullable=False)
    overall_progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User")
    occupation: Mapped["Occupation"] = relationship("Occupation", lazy="selectin")
    items: Mapped[list["RoadmapItem"]] = relationship(
        "RoadmapItem",
        back_populates="roadmap",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="RoadmapItem.id.asc()",
    )


class RoadmapItem(Base):
    """Individual phase learning milestone, topic, and project requirement item."""

    __tablename__ = "roadmap_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    roadmap_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("roadmaps.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    phase: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "Phase 1: Foundations"
    skill: Mapped[str] = mapped_column(String(100), nullable=False)
    topics: Mapped[list[str]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=list,
        nullable=False,
    )
    projects: Mapped[list[str]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=list,
        nullable=False,
    )
    resources: Mapped[list[str]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=list,
        nullable=False,
    )
    priority: Mapped[str] = mapped_column(String(50), default="High", nullable=False)
    estimated_effort: Mapped[str] = mapped_column(String(100), default="2 weeks", nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationship
    roadmap: Mapped["Roadmap"] = relationship("Roadmap", back_populates="items", lazy="selectin")
    progress_entries: Mapped[list["RoadmapProgress"]] = relationship(
        "RoadmapProgress",
        back_populates="roadmap_item",
        cascade="all, delete-orphan",
    )


class RoadmapProgress(Base):
    """Historical audit log for item completion status and notes."""

    __tablename__ = "roadmap_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    roadmap_item_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("roadmap_items.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(50), default="not_started", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    roadmap_item: Mapped["RoadmapItem"] = relationship("RoadmapItem", back_populates="progress_entries")
    user: Mapped["User"] = relationship("User")
