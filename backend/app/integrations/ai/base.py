"""
Abstract AI provider interface.

All AI backends (Ollama, OpenAI, etc.) must implement this interface.
"""

from abc import ABC, abstractmethod
from typing import Any


class AIProvider(ABC):
    """Abstract base class for AI service providers."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the AI service is reachable and operational.

        Returns:
            True if the service is available, False otherwise.
        """
        ...

    @abstractmethod
    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate a response from the AI model.

        Args:
            prompt: The input prompt.
            **kwargs: Provider-specific options.

        Returns:
            The generated text response.
        """
        ...
