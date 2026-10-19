from datetime import datetime
from enum import StrEnum

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from halo.config import get_settings

EMBEDDING_DIM = get_settings().embedding_dim


class Platform(StrEnum):
    instagram = "instagram"
    youtube = "youtube"
    telegram = "telegram"
    manual = "manual"


class VideoStatus(StrEnum):
    pending = "pending"
    analyzing = "analyzing"
    analyzed = "analyzed"
    failed = "failed"


class BriefStatus(StrEnum):
    draft = "draft"
    running = "running"
    done = "done"
    failed = "failed"


class ShortlistStatus(StrEnum):
    suggested = "suggested"
    starred = "starred"
    rejected = "rejected"
    contacted = "contacted"


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Brand(TimestampMixin, Base):
    """A brand and the context every search and draft runs against (Kuli's "brand memory")."""

    __tablename__ = "brands"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    pillars: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    no_go_topics: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    tone: Mapped[str] = mapped_column(Text, default="")
    languages: Mapped[list[str]] = mapped_column(ARRAY(String), default=lambda: ["uz", "ru"])
    past_campaigns: Mapped[str] = mapped_column(Text, default="")
    telegram_chat_id: Mapped[int | None] = mapped_column(BigInteger)

    briefs: Mapped[list["Brief"]] = relationship(back_populates="brand", cascade="all, delete-orphan")


class Creator(TimestampMixin, Base):
    __tablename__ = "creators"

    id: Mapped[int] = mapped_column(primary_key=True)
    display_name: Mapped[str] = mapped_column(String(200))
    bio: Mapped[str] = mapped_column(Text, default="")
    city: Mapped[str] = mapped_column(String(100), default="")
    contact: Mapped[str] = mapped_column(String(200), default="")
    telegram_user_id: Mapped[int | None] = mapped_column(BigInteger, unique=True)
    price_uzs: Mapped[int | None] = mapped_column(BigInteger)

    # Rolled up from video analyses by services.profile
    summary: Mapped[str] = mapped_column(Text, default="")
    languages: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    niche_tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    avg_quality: Mapped[float | None] = mapped_column(Float)
    avg_hook_strength: Mapped[float | None] = mapped_column(Float)
    brand_safety_risk: Mapped[str] = mapped_column(String(10), default="unknown")
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM))
    last_refreshed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    accounts: Mapped[list["CreatorAccount"]] = relationship(
        back_populates="creator", cascade="all, delete-orphan", lazy="selectin"
    )
    videos: Mapped[list["Video"]] = relationship(back_populates="creator", cascade="all, delete-orphan")


class CreatorAccount(Base):
    __tablename__ = "creator_accounts"
    __table_args__ = (UniqueConstraint("platform", "handle"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    creator_id: Mapped[int] = mapped_column(ForeignKey("creators.id", ondelete="CASCADE"))
    platform: Mapped[str] = mapped_column(String(20))
    handle: Mapped[str] = mapped_column(String(200))
    external_id: Mapped[str | None] = mapped_column(String(200))
    # Set when the creator connects their Instagram (Graph API) so we can pull their own Reels
    access_token: Mapped[str | None] = mapped_column(Text)
    followers: Mapped[int | None] = mapped_column(BigInteger)
    avg_views: Mapped[int | None] = mapped_column(BigInteger)
    engagement_rate: Mapped[float | None] = mapped_column(Float)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    creator: Mapped[Creator] = relationship(back_populates="accounts")


class Video(TimestampMixin, Base):
    __tablename__ = "videos"
    __table_args__ = (UniqueConstraint("platform", "external_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    creator_id: Mapped[int] = mapped_column(ForeignKey("creators.id", ondelete="CASCADE"))
    account_id: Mapped[int | None] = mapped_column(ForeignKey("creator_accounts.id", ondelete="SET NULL"))
    platform: Mapped[str] = mapped_column(String(20))
    external_id: Mapped[str] = mapped_column(String(200))
    url: Mapped[str] = mapped_column(Text, default="")
    media_url: Mapped[str | None] = mapped_column(Text)
    # Preview images, for platforms that give no video file (YouTube)
    frame_urls: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    local_path: Mapped[str | None] = mapped_column(Text)
    caption: Mapped[str] = mapped_column(Text, default="")
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    views: Mapped[int | None] = mapped_column(BigInteger)
    likes: Mapped[int | None] = mapped_column(BigInteger)
    comments: Mapped[int | None] = mapped_column(BigInteger)
    duration_s: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20), default=VideoStatus.pending)
    error: Mapped[str | None] = mapped_column(Text)

    creator: Mapped[Creator] = relationship(back_populates="videos")
    analysis: Mapped["VideoAnalysis | None"] = relationship(
        back_populates="video", cascade="all, delete-orphan", uselist=False, lazy="selectin"
    )


class VideoAnalysis(TimestampMixin, Base):
    """What Claude saw in one video: hook, pacing, tone, niche, brand safety."""

    __tablename__ = "video_analyses"

    id: Mapped[int] = mapped_column(primary_key=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), unique=True)
    summary: Mapped[str] = mapped_column(Text)
    hook: Mapped[str] = mapped_column(Text)
    hook_strength: Mapped[int] = mapped_column(Integer)
    pacing: Mapped[str] = mapped_column(String(50))
    setting: Mapped[str] = mapped_column(Text)
    energy: Mapped[str] = mapped_column(String(50))
    on_screen_tone: Mapped[str] = mapped_column(Text)
    languages: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    niche_tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    production_quality: Mapped[int] = mapped_column(Integer)
    authenticity: Mapped[int] = mapped_column(Integer)
    brand_safety_risk: Mapped[str] = mapped_column(String(10))
    brand_safety_flags: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    transcript: Mapped[str] = mapped_column(Text, default="")
    model: Mapped[str] = mapped_column(String(100))
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM))

    video: Mapped[Video] = relationship(back_populates="analysis")


class Brief(TimestampMixin, Base):
    __tablename__ = "briefs"

    id: Mapped[int] = mapped_column(primary_key=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(200))
    text: Mapped[str] = mapped_column(Text)
    # Kuli-style "keeps watching": standing briefs re-run on a schedule and push new matches
    standing: Mapped[bool] = mapped_column(Boolean, default=False)
    criteria: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(20), default=BriefStatus.draft)
    error: Mapped[str | None] = mapped_column(Text)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    brand: Mapped[Brand] = relationship(back_populates="briefs")
    entries: Mapped[list["ShortlistEntry"]] = relationship(
        back_populates="brief", cascade="all, delete-orphan", order_by="ShortlistEntry.score.desc()"
    )


class ShortlistEntry(TimestampMixin, Base):
    __tablename__ = "shortlist_entries"
    __table_args__ = (UniqueConstraint("brief_id", "creator_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    brief_id: Mapped[int] = mapped_column(ForeignKey("briefs.id", ondelete="CASCADE"))
    creator_id: Mapped[int] = mapped_column(ForeignKey("creators.id", ondelete="CASCADE"))
    score: Mapped[int] = mapped_column(Integer)
    reasons: Mapped[str] = mapped_column(Text)
    risks: Mapped[str] = mapped_column(Text, default="")
    evidence_video_ids: Mapped[list[int]] = mapped_column(ARRAY(Integer), default=list)
    outreach_language: Mapped[str | None] = mapped_column(String(5))
    outreach_message: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default=ShortlistStatus.suggested)
    notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    brief: Mapped[Brief] = relationship(back_populates="entries")
    creator: Mapped[Creator] = relationship(lazy="selectin")


class Translation(TimestampMixin, Base):
    """AI-written text (Halo writes in English) translated the first time someone reads it in another language."""

    __tablename__ = "translations"
    __table_args__ = (UniqueConstraint("lang", "source_hash"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    lang: Mapped[str] = mapped_column(String(5))
    source_hash: Mapped[str] = mapped_column(String(64))  # sha256 of the English text
    source: Mapped[str] = mapped_column(Text)
    text: Mapped[str] = mapped_column(Text)
