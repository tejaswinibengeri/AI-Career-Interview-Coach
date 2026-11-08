# app.integrations.ai
"""
AI provider package.

Usage
-----
Import ``get_ai_provider`` everywhere you need an AI backend:

    from app.integrations.ai import get_ai_provider

    provider = get_ai_provider()          # Gemini if key set, else Ollama
    result   = await provider.generate(prompt)

The selection logic:
  • GEMINI_API_KEY is set in .env  → GeminiProvider (google/gemini-2.0-flash-exp)
  • GEMINI_API_KEY is empty / unset → OllamaProvider (local llama3)
"""

from app.core.config import settings
from app.integrations.ai.base import AIProvider
from app.integrations.ai.ollama import OllamaProvider


def get_ai_provider() -> AIProvider:
    """Return the best available AI provider.

    Decision order:
    1. ``GeminiProvider`` — when ``GEMINI_API_KEY`` is set in the environment.
    2. ``OllamaProvider`` — fallback when no Gemini key is configured.

    Returns:
        An :class:`AIProvider` instance ready for ``await provider.generate()``.
    """
    if getattr(settings, "GEMINI_API_KEY", ""):
        from app.integrations.ai.gemini import GeminiProvider  # lazy import

        return GeminiProvider()
    return OllamaProvider()


__all__ = ["AIProvider", "OllamaProvider", "get_ai_provider"]
