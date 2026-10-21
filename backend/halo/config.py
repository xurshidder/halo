from functools import lru_cache
from typing import Literal
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="HALO_", extra="ignore")

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/halo"
    redis_url: str = "redis://localhost:6379/0"
    # "redis": an arq worker runs background jobs (Docker Compose). "inline": the API process
    # runs them itself, for hosts with one free service and no worker (Render, see render.yaml).
    jobs: Literal["redis", "inline"] = "redis"

    # One-service hosting (halo.api.site): the built web app to serve, and a shared password.
    web_dist: str = ""
    access_password: str | None = None

    # Claude. Without HALO_ANTHROPIC_API_KEY, the Anthropic SDK reads ANTHROPIC_API_KEY
    # (or an `ant auth login` profile) itself. The HALO_ name is for hosts that reserve
    # ANTHROPIC_API_KEY for something else.
    anthropic_api_key: str | None = None
    claude_model: str = "claude-opus-5-5"
    claude_effort_analysis: str = "medium"
    claude_effort_scoring: str = "medium"
    claude_effort_outreach: str = "low"
    claude_effort_translation: str = "low"

    # Video analysis
    frames_per_video: int = 8
    frame_width: int = 768
    max_video_seconds: int = 180
    media_dir: str = "/tmp/halo-media"

    # Speech-to-text (optional). Without a key, videos are analyzed from frames only.
    elevenlabs_api_key: str | None = None

    # Embeddings for look-alike search (optional). Without a key, look-alikes use tag overlap.
    voyage_api_key: str | None = None
    voyage_model: str = "voyage-3.5"
    embedding_dim: int = 1024

    # Sources
    youtube_api_key: str | None = None
    instagram_graph_version: str = "v23.0"

    # Telegram bot (replaces Kuli's Slack alerts)
    telegram_bot_token: str | None = None
    telegram_bot_username: str = "halo_uz_bot"
    secret_key: str = "change-me"  # signs brand <-> Telegram chat link codes

    # Scout agent
    shortlist_size: int = 10
    candidate_pool_size: int = 40
    scoring_concurrency: int = 5

    # Routines (Kuli-style "keeps watching")
    creator_refresh_hours: int = 24

    cors_origins: list[str] = ["http://localhost:5173"]

    @field_validator("database_url")
    @classmethod
    def _asyncpg_url(cls, url: str) -> str:
        """Accept the plain postgres:// URLs that hosts such as Neon and Render hand out."""
        parts = urlsplit(url)
        scheme = "postgresql+asyncpg" if parts.scheme in ("postgres", "postgresql") else parts.scheme
        params = parse_qsl(parts.query, keep_blank_values=True)
        if scheme == parts.scheme and not any(k in ("sslmode", "channel_binding") for k, _ in params):
            return url
        # asyncpg spells sslmode as ssl, and rejects libpq's channel_binding option.
        params = [("ssl" if k == "sslmode" else k, v) for k, v in params if k != "channel_binding"]
        return urlunsplit((scheme, parts.netloc, parts.path, urlencode(params), parts.fragment))


@lru_cache
def get_settings() -> Settings:
    return Settings()
