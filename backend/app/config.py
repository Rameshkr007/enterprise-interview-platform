from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn, model_validator, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────────
    APP_NAME: str = "Enterprise Interview Platform"
    APP_VERSION: str = "1.0.0"
    ENV: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False
    API_PREFIX: str = "/api/v1"
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # ── Security ─────────────────────────────────────────────────────────────
    SECRET_KEY: str = Field(..., min_length=32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ── Database ─────────────────────────────────────────────────────────────
    DATABASE_URL: PostgresDsn = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/interview_platform"
    )
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 40
    DB_POOL_TIMEOUT: int = 30
    DB_ECHO: bool = False

    # ── Redis ─────────────────────────────────────────────────────────────────
    REDIS_URL: RedisDsn = Field(default="redis://localhost:6379/0")
    REDIS_WS_CHANNEL_PREFIX: str = "ws:interview:"

    @field_validator("REDIS_URL", mode="before")
    @classmethod
    def clean_redis_url(cls, v: object) -> object:
        if isinstance(v, str):
            v = v.strip()
            # If user accidentally pasted the redis-cli command from dashboard
            if "-u " in v:
                v = v.split("-u ")[-1].strip().strip('"').strip("'")
            elif v.startswith("redis-cli"):
                for part in v.split():
                    if part.startswith("redis://") or part.startswith("rediss://"):
                        v = part
                        break
            # Upstash requires TLS (rediss://)
            if v.startswith("redis://") and "upstash.io" in v:
                v = "rediss://" + v[len("redis://"):]
        return v

    # ── Object Storage (S3-compatible) ────────────────────────────────────────
    S3_BUCKET_NAME: str = "interview-platform"
    S3_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    S3_ENDPOINT_URL: str | None = None  # Set for MinIO/local

    # ── OpenAI ────────────────────────────────────────────────────────────────
    OPENAI_API_KEY: str = Field(..., min_length=10)
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-large"
    OPENAI_EMBEDDING_DIMENSIONS: int = 3072
    OPENAI_CHAT_MODEL: str = "gpt-4o"
    OPENAI_FAST_MODEL: str = "gpt-4o-mini"
    OPENAI_WHISPER_MODEL: str = "whisper-1"
    OPENAI_REQUEST_TIMEOUT: int = 60

    # ── Audio Pipeline ────────────────────────────────────────────────────────
    AUDIO_SAMPLE_RATE: int = 16000
    AUDIO_CHUNK_DURATION_MS: int = 1000
    AUDIO_MIN_SILENCE_DURATION_MS: int = 500
    AUDIO_SILENCE_THRESHOLD_DB: float = -40.0
    FILLER_WORDS: list[str] = ["uh", "um", "er", "ah", "like", "you know", "basically", "literally"]

    # ── Interview Engine ──────────────────────────────────────────────────────
    MAX_QUESTIONS_PER_SESSION: int = 20
    DIFFICULTY_UPGRADE_THRESHOLD: float = 0.70
    DIFFICULTY_DOWNGRADE_THRESHOLD: float = 0.40
    LANGGRAPH_CHECKPOINT_TTL_HOURS: int = 24

    # ── Observability ─────────────────────────────────────────────────────────
    OTEL_EXPORTER_OTLP_ENDPOINT: str | None = None
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.ENV == "production":
            if self.DEBUG:
                raise ValueError("DEBUG must be False in production")
            if self.SECRET_KEY == "changeme":
                raise ValueError("SECRET_KEY must be changed in production")
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
