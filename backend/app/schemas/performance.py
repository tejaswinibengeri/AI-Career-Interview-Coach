"""
Pydantic schemas for Interview Performance Analytics and Placement Readiness APIs.
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class ScoreHistoryItem(BaseModel):
    """Real database interview session score history entry."""

    interview_number: int
    session_id: int
    role: str
    difficulty: str
    score: float
    date: datetime | None = None


class TopicPerformanceItem(BaseModel):
    """Categorized topic strength/weakness performance metric."""

    topic: str
    avg_score: float
    questions_count: int


class PerformanceResponse(BaseModel):
    """Response schema for GET /api/v1/performance."""

    model_config = ConfigDict(from_attributes=True)

    total_interviews: int
    average_score: float | None = None
    best_score: float | None = None
    latest_score: float | None = None
    improvement: float | None = None
    technical_score: float | None = None
    communication_score: float | None = None
    weak_topics: list[TopicPerformanceItem] = Field(default_factory=list)
    strong_topics: list[TopicPerformanceItem] = Field(default_factory=list)
    score_history: list[ScoreHistoryItem] = Field(default_factory=list)
    has_enough_data: bool = False
    status_message: str


class ReadinessMetricComponent(BaseModel):
    """Individual readiness formula component evaluation."""

    key: str
    name: str
    available: bool
    score: float | None = None
    raw_weight: float
    effective_weight_percentage: float
    status: str


class ReadinessResponse(BaseModel):
    """Response schema for GET /api/v1/readiness."""

    model_config = ConfigDict(from_attributes=True)

    overall_readiness_score: float | None = None
    level: str
    status_message: str
    available_metrics_count: int
    total_metrics_count: int
    breakdown: list[ReadinessMetricComponent] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
