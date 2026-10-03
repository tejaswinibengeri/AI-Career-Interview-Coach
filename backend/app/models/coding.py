"""
SQLAlchemy ORM models for Coding Challenge System (Module 12).
"""

from datetime import datetime
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base


class CodingChallenge(Base):
    """Coding challenge problem statement, sample tests, and official solution."""

    __tablename__ = "coding_challenges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(150), unique=True, index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(50), index=True, nullable=False)  # Python, SQL, DSA
    difficulty: Mapped[str] = mapped_column(String(20), index=True, nullable=False)  # Easy, Medium, Hard
    description: Mapped[str] = mapped_column(Text, nullable=False)
    starter_code: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(20), default="python", nullable=False)  # python, sql
    examples: Mapped[list[dict]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=list,
        nullable=False,
    )
    test_cases: Mapped[list[dict]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=list,
        nullable=False,
    )
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    sql_schema: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    submissions: Mapped[list["CodingSubmission"]] = relationship(
        "CodingSubmission",
        back_populates="challenge",
        cascade="all, delete-orphan",
        order_by="CodingSubmission.submitted_at.desc()",
    )


class CodingSubmission(Base):
    """User code submission record for a coding challenge."""

    __tablename__ = "coding_submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    challenge_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("coding_challenges.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    language: Mapped[str] = mapped_column(String(20), nullable=False)
    code: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(30), index=True, nullable=False
    )  # Passed, Failed, Time Limit Exceeded, Runtime Error, Syntax Error
    passed_test_cases: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_test_cases: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    execution_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User")
    challenge: Mapped["CodingChallenge"] = relationship("CodingChallenge", back_populates="submissions")
    results: Mapped[list["CodingResult"]] = relationship(
        "CodingResult",
        back_populates="submission",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class CodingResult(Base):
    """Individual test case execution result for a submission."""

    __tablename__ = "coding_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    submission_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("coding_submissions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    test_case_index: Mapped[int] = mapped_column(Integer, nullable=False)
    passed: Mapped[bool] = mapped_column(nullable=False)
    input_data: Mapped[str] = mapped_column(Text, nullable=False)
    expected_output: Mapped[str] = mapped_column(Text, nullable=False)
    actual_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    execution_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    submission: Mapped["CodingSubmission"] = relationship("CodingSubmission", back_populates="results")
