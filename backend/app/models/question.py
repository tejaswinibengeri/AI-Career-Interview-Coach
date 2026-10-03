"""
SQLAlchemy ORM models for Interview Question Bank and User Question Bookmarks.
"""

from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base


class Question(Base):
    """Question item in the interview question bank."""

    __tablename__ = "question_bank"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(
        String(50), index=True, nullable=False
    )  # Technical, HR, Behavioral, Coding, DSA, SQL, Aptitude, Role-specific
    difficulty: Mapped[str] = mapped_column(
        String(20), index=True, nullable=False
    )  # Easy, Medium, Hard
    role: Mapped[str] = mapped_column(
        String(100), index=True, default="General Software Engineer", nullable=False
    )
    tags: Mapped[list[str]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=list,
        nullable=False,
    )
    source_type: Mapped[str] = mapped_column(
        String(50), default="standard", index=True, nullable=False
    )  # standard, ai_generated
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    saved_by: Mapped[list["SavedQuestion"]] = relationship(
        "SavedQuestion",
        back_populates="question",
        cascade="all, delete-orphan",
    )


class SavedQuestion(Base):
    """User bookmarked saved interview question."""

    __tablename__ = "saved_questions"
    __table_args__ = (UniqueConstraint("user_id", "question_id", name="uq_user_question_saved"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    question_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("question_bank.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    saved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User")
    question: Mapped["Question"] = relationship("Question", back_populates="saved_by", lazy="selectin")
