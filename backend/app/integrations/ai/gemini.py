"""
Google Gemini AI provider implementation.

Connects to the Gemini API (generativelanguage.googleapis.com) using the
same AIProvider interface as OllamaProvider so all services work unchanged.
Shares the same in-memory LRU/TTL response cache used by Ollama.
"""

import logging
from typing import Any

import httpx

from app.core.config import settings
from app.integrations.ai.base import AIProvider
from app.integrations.ai.ollama import LLMResponseCache, get_shared_client, llm_cache

logger = logging.getLogger(__name__)

# Gemini REST endpoint (v1beta supports all public models incl. 2.0-flash)
_GEMINI_GENERATE_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)
_GEMINI_MODELS_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
)


class GeminiProvider(AIProvider):
    """AI provider backed by the Google Gemini API.

    Implements the same :class:`AIProvider` interface as :class:`OllamaProvider`
    so every service that calls ``provider.generate(prompt)`` works with zero
    functional changes.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float = 90.0,
    ):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL
        self.timeout = timeout

    # ------------------------------------------------------------------
    # AIProvider interface
    # ------------------------------------------------------------------

    async def health_check(self) -> bool:
        """Ping the Gemini API to verify the key is valid and service is reachable.

        Returns:
            True if Gemini responds successfully, False otherwise.
        """
        if not self.api_key:
            logger.warning("GEMINI_API_KEY is not set — Gemini provider is unavailable.")
            return False
        try:
            client = get_shared_client()
            url = "https://generativelanguage.googleapis.com/v1beta/models"
            headers = {"x-goog-api-key": self.api_key}
            response = await client.get(url, headers=headers, timeout=10.0)
            if response.status_code == 200:
                logger.debug("Gemini API is reachable.")
                return True
            logger.warning(
                "Gemini API returned status %d during health check: %s",
                response.status_code,
                response.text[:200],
            )
            return False
        except httpx.ConnectError:
            logger.warning("Cannot connect to Gemini API.")
            return False
        except httpx.TimeoutException:
            logger.warning("Timeout connecting to Gemini API.")
            return False
        except Exception as exc:
            logger.error("Unexpected error checking Gemini health: %s", exc)
            return False

    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate a response using the Gemini API.

        Args:
            prompt: The input prompt (sent as a single ``user`` turn).
            **kwargs: Accepts ``bypass_cache``, ``timeout``, and
                ``generation_config`` (dict) for Gemini-specific overrides.

        Returns:
            The generated text response.

        Raises:
            ConnectionError: If the API is unreachable or times out.
            RuntimeError: If the API returns a non-200 status or unexpected data.
        """
        bypass_cache = bool(kwargs.pop("bypass_cache", False))

        # Check in-memory cache (shared with OllamaProvider)
        cache_key = None
        if not bypass_cache:
            cache_key = llm_cache.make_key(f"gemini:{self.model}", prompt, kwargs)
            cached_val = llm_cache.get(cache_key)
            if cached_val is not None:
                logger.debug("LLM cache hit for Gemini model %s (0ms response)", self.model)
                return cached_val

        call_timeout = kwargs.pop("timeout", self.timeout)

        # Gemini generation config for maximum accuracy & zero hallucination:
        # - temperature: 0.0 forces purely deterministic, highest-probability factual output (no randomness, no creativity/guessing).
        # - topP: 0.1 restricts token sampling strictly to the absolute highest-confidence tokens.
        # - maxOutputTokens: 4096 gives ample room for complete, detailed, untruncated answers and JSON structures.
        default_generation_config: dict[str, Any] = {
            "temperature": 0.0,
            "topP": 0.1,
            "maxOutputTokens": 4096,
        }
        generation_config = dict(default_generation_config)
        if "generation_config" in kwargs and isinstance(kwargs["generation_config"], dict):
            generation_config.update(kwargs.pop("generation_config"))
        else:
            kwargs.pop("generation_config", None)

        # Ignore Ollama-specific kwargs that may be forwarded (options, format, keep_alive)
        for _key in ("options", "format", "keep_alive"):
            kwargs.pop(_key, None)

        # Universal, fully-dynamic system instruction — zero hardcoded roles or personas
        system_instruction = {
            "parts": [
                {
                    "text": (
                        "You are an advanced, domain-adaptive, ultra-precise reasoning engine. "
                        "Dynamically adapt your role, context, and domain strictly according to the task and prompt requested. "
                        "Never assume a rigid persona or default role unless specified in the prompt. "
                        "Deliver 100% accurate, factual, grounded, and verified analysis. "
                        "Do NOT make assumptions, guess, hallucinate, predict, or insert placeholder data. "
                        "Evaluate and respond strictly based on the exact inputs and verified domain knowledge provided."
                    )
                }
            ]
        }

        payload: dict[str, Any] = {
            "systemInstruction": system_instruction,
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": generation_config,
        }

        url = _GEMINI_GENERATE_URL.format(model=self.model)

        try:
            client = get_shared_client()
            headers = {"x-goog-api-key": self.api_key}
            response = await client.post(
                url,
                json=payload,
                params={"key": self.api_key},
                headers=headers,
                timeout=call_timeout,
            )

            if response.status_code == 429:
                raise RuntimeError(
                    "Gemini API rate limit exceeded. Please wait and retry."
                )
            if response.status_code == 401 or response.status_code == 403:
                raise RuntimeError(
                    "Gemini API key is invalid or lacks permission. "
                    "Check GEMINI_API_KEY in your .env file."
                )

            response.raise_for_status()
            data = response.json()

            # Extract text from Gemini response structure
            candidates = data.get("candidates", [])
            if not candidates:
                raise RuntimeError("Gemini returned no candidates in the response.")

            parts = candidates[0].get("content", {}).get("parts", [])
            result = "".join(p.get("text", "") for p in parts).strip()

            if not result:
                raise RuntimeError("Gemini returned an empty response.")

            # Store in shared cache
            if cache_key and result:
                llm_cache.set(cache_key, result)

            return result

        except httpx.ConnectError as exc:
            raise ConnectionError(
                "Cannot connect to Gemini API. Check your internet connection."
            ) from exc
        except httpx.TimeoutException as exc:
            raise ConnectionError(
                f"Gemini API request timed out after {call_timeout}s."
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Gemini API failed with status {exc.response.status_code}: "
                f"{exc.response.text[:200]}"
            ) from exc
        except (ConnectionError, RuntimeError):
            raise
        except Exception as exc:
            raise RuntimeError(f"Gemini generation error: {exc}") from exc

