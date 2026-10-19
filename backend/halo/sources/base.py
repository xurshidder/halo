from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol

from halo.models import CreatorAccount


class SourceError(RuntimeError):
    pass


@dataclass
class SourceVideo:
    external_id: str
    url: str
    caption: str = ""
    posted_at: datetime | None = None
    media_url: str | None = None  # a downloadable video file, when the platform gives one
    frame_urls: list[str] = field(default_factory=list)  # preview images when it does not
    views: int | None = None
    likes: int | None = None
    comments: int | None = None
    duration_s: float | None = None


@dataclass
class AccountSnapshot:
    external_id: str | None = None
    followers: int | None = None
    videos: list[SourceVideo] = field(default_factory=list)

    @property
    def avg_views(self) -> int | None:
        views = [v.views for v in self.videos if v.views is not None]
        return int(sum(views) / len(views)) if views else None

    @property
    def engagement_rate(self) -> float | None:
        """(likes + comments) / followers, averaged over recent videos."""
        if not self.followers:
            return None
        rates = [
            ((v.likes or 0) + (v.comments or 0)) / self.followers
            for v in self.videos
            if v.likes is not None or v.comments is not None
        ]
        return round(sum(rates) / len(rates), 4) if rates else None


class VideoSource(Protocol):
    async def fetch(self, account: CreatorAccount, limit: int = 12) -> AccountSnapshot: ...
