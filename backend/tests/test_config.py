"""
Tests for configuration loading.
"""

from app.core.config import Settings


def test_default_settings_load():
    """Settings should load with sensible defaults even without a .env file."""
    s = Settings(
        _env_file=None,
        DATABASE_URL="postgresql+asyncpg://test:test@localhost:5432/test",
        DATABASE_URL_SYNC="postgresql://test:test@localhost:5432/test",
    )
    assert s.APP_NAME == "AI Career & Interview Coach"
    assert s.APP_VERSION == "0.1.0"
    assert s.JWT_ALGORITHM == "HS256"
    assert s.JWT_EXPIRATION_MINUTES == 30
    assert s.OLLAMA_MODEL == "llama3"


def test_cors_origins_parsing_from_json_string():
    """CORS_ORIGINS should parse a JSON array string correctly."""
    s = Settings(
        CORS_ORIGINS='["http://localhost:3000","http://example.com"]',
        DATABASE_URL="postgresql+asyncpg://test:test@localhost:5432/test",
        DATABASE_URL_SYNC="postgresql://test:test@localhost:5432/test",
    )
    assert s.CORS_ORIGINS == ["http://localhost:3000", "http://example.com"]


def test_cors_origins_parsing_from_comma_separated():
    """CORS_ORIGINS should parse a comma-separated string correctly."""
    s = Settings(
        CORS_ORIGINS="http://a.com, http://b.com",
        DATABASE_URL="postgresql+asyncpg://test:test@localhost:5432/test",
        DATABASE_URL_SYNC="postgresql://test:test@localhost:5432/test",
    )
    assert s.CORS_ORIGINS == ["http://a.com", "http://b.com"]


def test_debug_defaults_to_false():
    """DEBUG should default to False when env does not override."""
    s = Settings(
        _env_file=None,
        DATABASE_URL="postgresql+asyncpg://test:test@localhost:5432/test",
        DATABASE_URL_SYNC="postgresql://test:test@localhost:5432/test",
    )
    assert s.DEBUG is False
