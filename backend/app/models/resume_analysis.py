"""
SQLAlchemy models for Resume Analysis and Extracted Resume Skills.
"""

from datetime import datetime
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base


class ResumeAnalysis(Base):
    """AI Analysis and ATS evaluation for a specific resume version."""

    __tablename__ = "resume_analysis"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resume_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("resumes.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    resume_version_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("resume_versions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    ats_score: Mapped[float] = mapped_column(Float, nullable=False)
    scoring_breakdown: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
    )
    experience_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    education_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    project_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    certifications: Mapped[list[str]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=list,
        nullable=False,
    )
    strengths: Mapped[list[str]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=list,
        nullable=False,
    )
    weaknesses: Mapped[list[str]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=list,
        nullable=False,
    )
    missing_keywords: Mapped[list[str]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=list,
        nullable=False,
    )
    grammar_suggestions: Mapped[list[str]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=list,
        nullable=False,
    )
    formatting_suggestions: Mapped[list[str]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=list,
        nullable=False,
    )
    improvement_recommendations: Mapped[list[str]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=list,
        nullable=False,
    )
    raw_ai_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    resume: Mapped["Resume"] = relationship("Resume", back_populates="analyses")
    version: Mapped["ResumeVersion"] = relationship("ResumeVersion")
    user: Mapped["User"] = relationship("User")
    skills: Mapped[list["ResumeSkill"]] = relationship(
        "ResumeSkill",
        back_populates="analysis",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ResumeSkill(Base):
    """Structured technical or soft skill extracted from resume analysis."""

    __tablename__ = "resume_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resume_analysis_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("resume_analysis.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    skill_name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="technical")
    proficiency_level: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Relationship
    analysis: Mapped["ResumeAnalysis"] = relationship("ResumeAnalysis", back_populates="skills")
