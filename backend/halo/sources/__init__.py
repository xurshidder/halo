from halo.models import Platform
from halo.sources.base import VideoSource
from halo.sources.instagram import InstagramSource
from halo.sources.youtube import YouTubeSource


def get_source(platform: str) -> VideoSource | None:
    """The connector for a platform, or None (manual uploads and Telegram have no API pull)."""
    if platform == Platform.youtube:
        return YouTubeSource()
    if platform == Platform.instagram:
        return InstagramSource()
    return None
