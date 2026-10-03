"""
SQLAlchemy ORM models for Occupations, Skills, Career Goals, and Skill Gap Reports.
"""

from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base


class Occupation(Base):
    """O*NET / Legitimate career occupation entity."""

    __tablename__ = "occupations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    industry: Mapped[str] = mapped_column(String(100), default="Information Technology", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    skills: Mapped[list["OccupationSkill"]] = relationship(
        "OccupationSkill",
        back_populates="occupation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    career_goals: Mapped[list["CareerGoal"]] = relationship(
        "CareerGoal",
        back_populates="occupation",
        cascade="all, delete-orphan",
    )


class Skill(Base):
    """Global taxonomy skill entity."""

    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="technical", nullable=False)


class OccupationSkill(Base):
    """Mapping between an Occupation and its required Skill with importance/level weights."""

    __tablename__ = "occupation_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    occupation_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("occupations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    skill_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("skills.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    importance: Mapped[float] = mapped_column(Float, default=80.0, nullable=False)
    level: Mapped[float] = mapped_column(Float, default=70.0, nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    occupation: Mapped["Occupation"] = relationship("Occupation", back_populates="skills")
    skill: Mapped["Skill"] = relationship("Skill", lazy="selectin")


class UserSkill(Base):
    """Skills associated with an authenticated user from profile, resume, or manual entries."""

    __tablename__ = "user_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    skill_name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    source: Mapped[str] = mapped_column(String(50), default="profile", nullable=False)
    proficiency: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class CareerGoal(Base):
    """User target career goal."""

    __tablename__ = "career_goals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    occupation_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("occupations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    target_role_title: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User")
    occupation: Mapped["Occupation"] = relationship("Occupation", back_populates="career_goals", lazy="selectin")


class SkillGapReport(Base):
    """Generated skill gap analysis report comparing user skills against occupation requirements."""

    __tablename__ = "skill_gap_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    occupation_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("occupations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    match_percentage: Mapped[float] = mapped_column(Float, nullable=False)
    strong_skills: Mapped[list[dict]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=list,
        nullable=False,
    )
    intermediate_skills: Mapped[list[dict]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=list,
        nullable=False,
    )
    missing_skills: Mapped[list[dict]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=list,
        nullable=False,
    )
    learning_order: Mapped[list[dict]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=list,
        nullable=False,
    )
    ai_explanation: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User")
    occupation: Mapped["Occupation"] = relationship("Occupation", lazy="selectin")
