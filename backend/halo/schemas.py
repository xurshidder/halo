from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from halo.models import Platform, ShortlistStatus


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class BrandIn(BaseModel):
    name: str
    description: str = ""
    pillars: list[str] = []
    no_go_topics: list[str] = []
    tone: str = ""
    languages: list[str] = ["uz", "ru"]
    past_campaigns: str = ""


class BrandPatch(BaseModel):
    name: str | None = None
    description: str | None = None
    pillars: list[str] | None = None
    no_go_topics: list[str] | None = None
    tone: str | None = None
    languages: list[str] | None = None
    past_campaigns: str | None = None


class BrandOut(ORM):
    id: int
    name: str
    description: str
    pillars: list[str]
    no_go_topics: list[str]
    tone: str
    languages: list[str]
    past_campaigns: str
    telegram_connected: bool = False
    created_at: datetime


class AccountIn(BaseModel):
    platform: Platform
    handle: str
    external_id: str | None = None
    access_token: str | None = Field(default=None, description="Instagram token from Instagram Login")


class AccountOut(ORM):
    id: int
    platform: str
    handle: str
    followers: int | None
    avg_views: int | None
    engagement_rate: float | None
    last_synced_at: datetime | None


class CreatorIn(BaseModel):
    display_name: str
    bio: str = ""
    city: str = ""
    contact: str = ""
    price_uzs: int | None = None
    accounts: list[AccountIn] = []


class CreatorOut(ORM):
    id: int
    display_name: str
    bio: str
    city: str
    contact: str
    price_uzs: int | None
    summary: str
    languages: list[str]
    niche_tags: list[str]
    avg_quality: float | None
    avg_hook_strength: float | None
    brand_safety_risk: str
    last_refreshed_at: datetime | None
    accounts: list[AccountOut]


class AnalysisOut(ORM):
    summary: str
    hook: str
    hook_strength: int
    pacing: str
    setting: str
    energy: str
    on_screen_tone: str
    languages: list[str]
    niche_tags: list[str]
    production_quality: int
    authenticity: int
    brand_safety_risk: str
    brand_safety_flags: list[str]
    transcript: str


class VideoOut(ORM):
    id: int
    platform: str
    url: str
    caption: str
    posted_at: datetime | None
    views: int | None
    likes: int | None
    comments: int | None
    duration_s: float | None
    status: str
    error: str | None
    analysis: AnalysisOut | None


class CreatorDetail(CreatorOut):
    videos: list[VideoOut] = []


class VideoUrlIn(BaseModel):
    url: str = Field(description="A direct link to a video file (.mp4)")
    caption: str = ""


class LookalikeOut(BaseModel):
    creator: CreatorOut
    similarity: float


class BriefIn(BaseModel):
    title: str
    text: str
    standing: bool = False


class EntryOut(ORM):
    id: int
    creator: CreatorOut
    score: int
    reasons: str
    risks: str
    evidence_video_ids: list[int]
    outreach_language: str | None
    outreach_message: str | None
    status: str
    notified_at: datetime | None


class EntryPatch(BaseModel):
    status: ShortlistStatus | None = None
    outreach_message: str | None = None


class BriefOut(ORM):
    id: int
    brand_id: int
    title: str
    text: str
    standing: bool
    criteria: dict | None
    status: str
    error: str | None
    created_at: datetime
    completed_at: datetime | None


class BriefDetail(BriefOut):
    entries: list[EntryOut] = []


class JobOut(BaseModel):
    queued: str
    id: int


class TelegramLinkOut(BaseModel):
    url: str
    connected: bool
