"""
Tests for the Ollama AI provider.
"""

import pytest

from app.integrations.ai.ollama import OllamaProvider


@pytest.mark.asyncio
async def test_ollama_health_check_handles_unreachable():
    """OllamaProvider should return False when Ollama is not reachable."""
    provider = OllamaProvider(base_url="http://localhost:99999", timeout=2.0)
    result = await provider.health_check()
    assert result is False


@pytest.mark.asyncio
async def test_ollama_generate_raises_when_unavailable():
    """OllamaProvider.generate() should raise ConnectionError when Ollama is down."""
    provider = OllamaProvider(base_url="http://localhost:99999", timeout=2.0)
    with pytest.raises(ConnectionError):
        await provider.generate("Hello")


def test_ollama_provider_uses_config_defaults():
    """OllamaProvider should pick up config defaults when no args are given."""
    provider = OllamaProvider()
    assert "localhost" in provider.base_url or "host.docker.internal" in provider.base_url
    assert provider.model is not None


def test_llm_response_cache():
    """LLMResponseCache should cache responses and retrieve them before TTL expiration."""
    from app.integrations.ai.ollama import LLMResponseCache

    cache = LLMResponseCache(maxsize=3, default_ttl=60.0)
    key1 = cache.make_key("llama3.2:3b", "hello", {})
    key2 = cache.make_key("llama3.2:3b", "world", {})

    cache.set(key1, "response 1")
    assert cache.get(key1) == "response 1"
    assert cache.get(key2) is None

    # Test TTL expiration
    cache.set(key2, "response 2", ttl=-1.0)  # already expired
    assert cache.get(key2) is None

    # Test LRU eviction
    cache.set("k1", "v1")
    cache.set("k2", "v2")
    cache.set("k3", "v3")
    cache.set("k4", "v4")  # k1 should be evicted (maxsize=3)
    assert cache.get("k1") is None
    assert cache.get("k4") == "v4"


@pytest.mark.asyncio
async def test_ollama_warmup_handles_offline():
    """warmup should return False gracefully when Ollama is offline."""
    provider = OllamaProvider(base_url="http://localhost:99999", timeout=1.0)
    result = await provider.warmup()
    assert result is False

