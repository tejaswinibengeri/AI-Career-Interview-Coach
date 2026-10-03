"""
Abstract Base Interface for Career Data Providers.
Allows switching or combining multiple data sources (e.g., O*NET, ESCO, custom APIs).
"""

from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel, Field


class CareerSkillData(BaseModel):
    """Skill requirement for an occupation."""

    name: str
    category: str = "technical"  # "technical", "soft", "tool", "knowledge"
    importance: float = 80.0  # 0 to 100
    level: float = 70.0  # 0 to 100
    is_required: bool = True


class OccupationData(BaseModel):
    """Standardized occupation entity."""

    code: str  # e.g., O*NET SOC code "15-1252.00"
    title: str
    description: str
    industry: str = "Information Technology"
    skills: list[CareerSkillData] = Field(default_factory=list)


class CareerDataProvider(ABC):
    """Abstract contract for retrieving legitimate career and occupation datasets."""

    @abstractmethod
    async def search_occupations(self, query: str, limit: int = 20) -> list[OccupationData]:
        """Search occupations by keyword or title query."""
        pass

    @abstractmethod
    async def get_occupation_details(self, code: str) -> OccupationData | None:
        """Fetch detailed occupation profile including required skills."""
        pass
