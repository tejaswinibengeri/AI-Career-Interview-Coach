"""
Core configuration — loads all settings from environment variables via Pydantic Settings.
"""

from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide settings loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    APP_NAME: str = "AI Career & Interview Coach"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # --- Database ---
    DATABASE_URL: str = "sqlite+aiosqlite:///./career_coach.db"
    DATABASE_URL_SYNC: str = "sqlite:///./career_coach.db"

    # --- Security / JWT ---
    JWT_SECRET: str = "change-me-to-a-random-secret-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 30
    RATE_LIMIT_ENABLED: bool = True
    MAX_REQUEST_BODY_BYTES: int = 15 * 1024 * 1024  # 15 MB

    # --- Ollama AI ---
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"

    # --- Google Gemini AI ---
    # Set GEMINI_API_KEY to switch from Ollama → Gemini automatically.
    # Leave empty (or omit) to keep using Ollama as the AI backend.
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.8-flash"

    # --- Storage / Uploads ---
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB

    # --- Job Provider (Configurable API) ---
    JOB_PROVIDER_API_KEY: str = ""
    JOB_PROVIDER_API_ID: str = ""
    JOB_PROVIDER_URL: str = ""
    ADZUNA_APP_ID: str = ""
    ADZUNA_APP_KEY: str = ""
    ADZUNA_COUNTRY: str = "us"

    # --- n8n Webhook Integration ---
    N8N_WEBHOOK_URL: str = ""

    # --- Email / SMTP Notifications ---
    SMTP_ENABLED: bool = False
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_NAME: str = "CareerCoachAI"

    # --- Scheduled Reminders ---
    REMINDER_MORNING_TIME: str = "08:00"  # HH:MM 24-hour format
    REMINDER_EVENING_TIME: str = "20:00"  # HH:MM 24-hour format
    REMINDER_TIMEZONE: str = "Asia/Kolkata"  # e.g., Asia/Kolkata, America/New_York, UTC

    # --- CORS ---
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:3000",
        "http://localhost:4173",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:4173",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator("DATABASE_URL", "DATABASE_URL_SYNC", mode="after")
    @classmethod
    def resolve_sqlite_path(cls, v: str) -> str:
        if v.startswith("sqlite") and "///./" in v:
            from pathlib import Path
            backend_dir = Path(__file__).resolve().parent.parent.parent
            rel_part = v.split("///./")[-1]
            abs_db = (backend_dir / rel_part).resolve()
            prefix = v.split("///./")[0] + "///"
            return f"{prefix}{abs_db.as_posix()}"
        return v

    @field_validator("JWT_SECRET", mode="after")
    @classmethod
    def validate_jwt_secret(cls, v: str, info) -> str:
        # Require strong non-placeholder secrets in production
        import os
        env = os.getenv("ENVIRONMENT", "development").lower()
        if env == "production":
            if v == "change-me-to-a-random-secret-in-production" or len(v) < 32:
                raise ValueError(
                    "Insecure JWT_SECRET: In production, JWT_SECRET must be at least 32 characters and cannot use default placeholders."
                )
        return v

    @field_validator("UPLOAD_DIR", mode="after")
    @classmethod
    def resolve_upload_dir(cls, v: str) -> str:
        from pathlib import Path
        upload_path = Path(v)
        if not upload_path.is_absolute():
            backend_dir = Path(__file__).resolve().parent.parent.parent
            return str((backend_dir / upload_path).resolve())
        return v


# Singleton — import this everywhere
settings = Settings()
