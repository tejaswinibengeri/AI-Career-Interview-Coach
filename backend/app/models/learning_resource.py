"""
SQLAlchemy ORM models for Learning Resources System (Module 14).
"""

from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class LearningResource(Base):
    """Catalog of verified learning resources connected to skill gaps."""

    __tablename__ = "learning_resources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    source: Mapped[str] = mapped_column(String(100), index=True, nullable=False)  # Official Documentation, freeCodeCamp, Coursera, YouTube, etc.
    resource_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)  # Documentation, Course, Video, Book, Certification
    skill_name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)  # Python, FastAPI, React, PostgreSQL, Docker, etc.
    difficulty: Mapped[str] = mapped_column(String(20), index=True, nullable=False)  # Beginner, Intermediate, Advanced
    estimated_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user_progress: Mapped[list["UserLearningProgress"]] = relationship(
        "UserLearningProgress",
        back_populates="resource",
        cascade="all, delete-orphan",
    )


class UserLearningProgress(Base):
    """User progress tracking (saved resources and completion status)."""

    __tablename__ = "user_learning_progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    resource_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("learning_resources.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    is_saved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User")
    resource: Mapped["LearningResource"] = relationship("LearningResource", back_populates="user_progress")
