"""
Ollama AI provider implementation.

Connects to a local or remote Ollama instance with high-performance connection
pooling, GPU keep-alive, unified context management, and in-memory TTL caching.
"""

import hashlib
import logging
import time
from collections import OrderedDict
from typing import Any

import httpx

from app.core.config import settings
from app.integrations.ai.base import AIProvider

logger = logging.getLogger(__name__)


class LLMResponseCache:
    """High-speed in-memory LRU cache with TTL expiration for LLM responses."""

    def __init__(self, maxsize: int = 500, default_ttl: float = 1800.0):
        self.maxsize = maxsize
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, tuple[float, str]] = OrderedDict()

    @staticmethod
    def make_key(model: str, prompt: str, kwargs: dict[str, Any]) -> str:
        """Create a deterministic SHA-256 cache key from request parameters."""
        filtered_kwargs = {
            k: v for k, v in kwargs.items() if k not in ("bypass_cache", "timeout")
        }
        sorted_repr = sorted((str(k), str(v)) for k, v in filtered_kwargs.items())
        raw = f"{model}:{prompt}:{sorted_repr}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, key: str) -> str | None:
        """Retrieve unexpired cached response or return None."""
        now = time.time()
        if key in self._cache:
            exp, val = self._cache[key]
            if now < exp:
                self._cache.move_to_end(key)
                return val
            # Expired
            del self._cache[key]
        return None

    def set(self, key: str, val: str, ttl: float | None = None) -> None:
        """Store response with TTL and enforce LRU maxsize."""
        now = time.time()
        exp = now + (ttl if ttl is not None else self.default_ttl)
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = (exp, val)
        if len(self._cache) > self.maxsize:
            self._cache.popitem(last=False)

    def clear(self) -> None:
        """Flush the cache."""
        self._cache.clear()


# Global response cache singleton
llm_cache = LLMResponseCache(maxsize=500, default_ttl=1800.0)

# Global shared HTTP client for connection reuse
_shared_client: httpx.AsyncClient | None = None


def get_shared_client() -> httpx.AsyncClient:
    """Obtain or initialize the persistent httpx.AsyncClient with connection pooling."""
    global _shared_client
    if _shared_client is None or _shared_client.is_closed:
        _shared_client = httpx.AsyncClient(
            limits=httpx.Limits(
                max_keepalive_connections=20,
                max_connections=50,
                keepalive_expiry=60.0,
            ),
            timeout=httpx.Timeout(90.0, connect=10.0),
        )
    return _shared_client


async def close_shared_client() -> None:
    """Gracefully close the persistent HTTP client on shutdown."""
    global _shared_client
    if _shared_client is not None and not _shared_client.is_closed:
        await _shared_client.aclose()
        _shared_client = None


class OllamaProvider(AIProvider):
    """High-performance AI provider backed by an Ollama instance."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 90.0,
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.timeout = timeout

    async def health_check(self) -> bool:
        """Ping the Ollama API to verify it is reachable.

        Returns:
            True if Ollama responds successfully.
        """
        try:
            client = get_shared_client()
            response = await client.get(
                f"{self.base_url}/api/tags",
                timeout=min(self.timeout, 10.0),
            )
            if response.status_code == 200:
                logger.debug("Ollama is reachable at %s", self.base_url)
                return True
            logger.warning("Ollama returned status %d from %s", response.status_code, self.base_url)
            return False
        except httpx.ConnectError:
            logger.warning("Cannot connect to Ollama at %s", self.base_url)
            return False
        except httpx.TimeoutException:
            logger.warning("Timeout connecting to Ollama at %s", self.base_url)
            return False
        except Exception as exc:
            logger.error("Unexpected error checking Ollama health: %s", exc)
            return False

    async def get_available_models(self) -> list[str]:
        """Fetch list of available model names from Ollama tags."""
        try:
            client = get_shared_client()
            response = await client.get(f"{self.base_url}/api/tags", timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                return [m.get("name", "") for m in data.get("models", []) if m.get("name")]
        except Exception as exc:
            logger.debug("Could not fetch available Ollama models: %s", exc)
        return []

    async def warmup(self) -> bool:
        """Preload model weights into GPU VRAM to eliminate user cold-start latency."""
        try:
            client = get_shared_client()
            payload = {
                "model": self.model,
                "prompt": "ping",
                "stream": False,
                "keep_alive": "60m",
                "options": {"num_predict": 1, "num_ctx": 4096},
            }
            resp = await client.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=20.0,
            )
            if resp.status_code == 200:
                logger.info("Ollama model '%s' pre-warmed successfully (keep_alive=60m).", self.model)
                return True
        except Exception as exc:
            logger.debug("Ollama warmup deferred or offline: %s", exc)
        return False

    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate a response using the Ollama API with caching, keep-alive, and speed optimizations.

        Args:
            prompt: The input prompt.
            **kwargs: Additional options (format, options, bypass_cache, timeout, etc.).

        Returns:
            The generated text response.
        """
        bypass_cache = bool(kwargs.pop("bypass_cache", False))

        # Check in-memory cache for instant <1ms response
        cache_key = None
        if not bypass_cache:
            cache_key = llm_cache.make_key(self.model, prompt, kwargs)
            cached_val = llm_cache.get(cache_key)
            if cached_val is not None:
                logger.debug("LLM cache hit for model %s (0ms response)", self.model)
                return cached_val

        call_timeout = kwargs.pop("timeout", None)
        if call_timeout is None:
            # Respect self.timeout (default 90.0s) or custom short timeout for tests
            call_timeout = self.timeout

        try:
            client = get_shared_client()

            # Unified, high-accuracy generation defaults:
            # num_ctx=4096 ensures complete prompts and context fit easily without truncation
            # num_predict=1000 ensures structured JSON responses are never truncated mid-object
            default_options: dict[str, Any] = {
                "num_predict": 1000,
                "num_ctx": 4096,
                "temperature": 0.2,
                "top_p": 0.9,
            }
            options = dict(default_options)
            if "options" in kwargs and isinstance(kwargs["options"], dict):
                options.update(kwargs["options"])

            payload: dict[str, Any] = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "keep_alive": "60m",  # Keep loaded in GPU VRAM for 60m
                "options": options,
                **{k: v for k, v in kwargs.items() if k != "options"},
            }

            response = await client.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=call_timeout,
            )

            # If model name failed with 404, attempt fallback to other installed model
            if response.status_code == 404:
                available = await self.get_available_models()
                alt_model = None
                for candidate in ["llama3.2:3b", "llama3:latest", "llama3"]:
                    if any(candidate in m for m in available):
                        alt_model = next(m for m in available if candidate in m)
                        break
                if alt_model and alt_model != self.model:
                    logger.info("Retrying with available Ollama model '%s' instead of '%s'", alt_model, self.model)
                    payload["model"] = alt_model
                    response = await client.post(
                        f"{self.base_url}/api/generate",
                        json=payload,
                        timeout=call_timeout,
                    )

            response.raise_for_status()
            data = response.json()
            result = data.get("response", "")

            # Store in cache
            if cache_key and result:
                llm_cache.set(cache_key, result)

            return result

        except httpx.ConnectError as exc:
            raise ConnectionError(
                f"Cannot connect to Ollama at {self.base_url}. Ensure Ollama is running."
            ) from exc
        except httpx.TimeoutException as exc:
            raise ConnectionError(
                f"Ollama request to {self.base_url} timed out after {call_timeout}s."
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Ollama generation failed with status {exc.response.status_code}"
            ) from exc
        except (OverflowError, ExceptionGroup) as exc:
            raise ConnectionError(
                f"Cannot connect to Ollama at {self.base_url}. Check the URL and port."
            ) from exc
        except Exception as exc:
            raise RuntimeError(f"Ollama generation error: {exc}") from exc
