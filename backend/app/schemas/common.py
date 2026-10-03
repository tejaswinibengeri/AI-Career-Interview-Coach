"""
Standard API response schemas used across all endpoints.
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard envelope for all successful API responses."""

    status: str = "success"
    data: T | None = None
    message: str = ""


class ErrorResponse(BaseModel):
    """Standard envelope for error responses."""

    status: str = "error"
    message: str = "An error occurred"
    details: Any | None = None


class HealthData(BaseModel):
    """Data payload for the health check endpoint."""

    status: str
    version: str
    database: str
    ollama: str
