"""Instagram API with Instagram Login: a connected creator's own Reels.

Creators who connect their account give us a token, and the API returns their
media with a downloadable `media_url`, so Halo can watch the actual video. Accounts
that have not connected are skipped here; they can still send videos to the
Telegram bot. Using this in production needs a Meta app with
instagram_business_basic and instagram_business_manage_insights approved.
"""

from datetime import datetime

import httpx

from halo.config import get_settings
from halo.models import CreatorAccount
from halo.sources.base import AccountSnapshot, SourceError, SourceVideo

API = "https://graph.instagram.com"
MEDIA_FIELDS = "id,caption,media_type,media_product_type,media_url,permalink,thumbnail_url,timestamp,like_count,comments_count"


class InstagramSource:
    def __init__(self, transport: httpx.AsyncBaseTransport | None = None):
        self.version = get_settings().instagram_graph_version
        self.transport = transport

    async def fetch(self, account: CreatorAccount, limit: int = 12) -> AccountSnapshot:
        if not account.access_token:
            raise SourceError(f"Instagram @{account.handle} is not connected (no access token)")
        token = account.access_token
        async with httpx.AsyncClient(base_url=f"{API}/{self.version}", timeout=30, transport=self.transport) as http:
            me = await self._get(http, "/me", {"fields": "user_id,username,followers_count", "access_token": token})
            media = await self._get(
                http, "/me/media", {"fields": MEDIA_FIELDS, "limit": limit * 2, "access_token": token}
            )
            videos = []
            for item in media.get("data", []):
                if item.get("media_type") != "VIDEO":
                    continue
                video = self._to_video(item)
                video.views = await self._views(http, item["id"], token)
                videos.append(video)
                if len(videos) >= limit:
                    break
        return AccountSnapshot(
            external_id=str(me.get("user_id") or me.get("id") or ""),
            followers=me.get("followers_count"),
            videos=videos,
        )

    @staticmethod
    async def _get(http: httpx.AsyncClient, path: str, params: dict) -> dict:
        resp = await http.get(path, params=params)
        if resp.status_code != 200:
            raise SourceError(f"Instagram API {path} returned {resp.status_code}: {resp.text[:300]}")
        return resp.json()

    @staticmethod
    async def _views(http: httpx.AsyncClient, media_id: str, token: str) -> int | None:
        """Views come from the insights endpoint; missing permission just means no number."""
        resp = await http.get(f"/{media_id}/insights", params={"metric": "views", "access_token": token})
        if resp.status_code != 200:
            return None
        for metric in resp.json().get("data", []):
            if metric.get("name") == "views" and metric.get("values"):
                return metric["values"][0].get("value")
        return None

    @staticmethod
    def _to_video(item: dict) -> SourceVideo:
        ts = item.get("timestamp")
        return SourceVideo(
            external_id=item["id"],
            url=item.get("permalink", ""),
            caption=item.get("caption", ""),
            posted_at=datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S%z") if ts else None,
            media_url=item.get("media_url"),
            frame_urls=[item["thumbnail_url"]] if item.get("thumbnail_url") else [],
            likes=item.get("like_count"),
            comments=item.get("comments_count"),
        )
