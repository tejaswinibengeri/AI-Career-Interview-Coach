"""
Pydantic schemas for Coding Challenge System (Module 12).
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class ExampleItem(BaseModel):
    """Problem example demonstration."""

    input: str
    output: str
    explanation: str | None = None


class SubmitCodeRequest(BaseModel):
    """Request payload to submit or run code for execution."""

    code: str = Field(..., min_length=2, description="Candidate source code")
    language: str = Field("python", description="python or sql")


class CodingResultResponse(BaseModel):
    """Response schema for individual test case execution result."""

    model_config = ConfigDict(from_attributes=True)

    test_case_index: int
    input_data: str
    expected_output: str
    passed: bool
    actual_output: str | None = None
    error_output: str | None = None
    execution_time_ms: float = 0.0


class CodingSubmissionResponse(BaseModel):
    """Response schema for a candidate code submission record."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    challenge_id: int
    language: str
    code: str
    status: str
    passed_test_cases: int
    total_test_cases: int
    execution_time_ms: float | None = None
    error_message: str | None = None
    results: list[CodingResultResponse] = Field(default_factory=list)
    submitted_at: datetime


class CodingChallengeResponse(BaseModel):
    """Response schema for coding challenge details and list."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    slug: str
    category: str
    difficulty: str
    description: str
    starter_code: str
    language: str
    examples: list[dict] = Field(default_factory=list)
    sample_test_cases: list[dict] = Field(default_factory=list)
    explanation: str | None = None
    sql_schema: str | None = None
    is_solved: bool = False
    created_at: datetime


class AIHintResponse(BaseModel):
    """Response schema for Ollama AI hints and code explanations."""

    hint: str
    explanation: str
