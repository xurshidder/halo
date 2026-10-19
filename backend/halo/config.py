from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="HALO_", extra="ignore")

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/halo"
    redis_url: str = "redis://localhost:6379/0"

    # Claude. The API key itself is read by the Anthropic SDK from ANTHROPIC_API_KEY.
    claude_model: str = "claude-opus-5-5"
    claude_effort_analysis: str = "medium"
    claude_effort_scoring: str = "medium"
    claude_effort_outreach: str = "low"

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


@lru_cache
def get_settings() -> Settings:
    return Settings()
