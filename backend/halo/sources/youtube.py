"""YouTube Data API v3: a channel's recent uploads and their stats.

The API gives no downloadable video file, and downloading YouTube videos breaks its
terms, so YouTube videos are analyzed from the preview frames YouTube publishes
(the thumbnail plus three auto-generated stills at roughly 25%, 50% and 75%).
"""

import re
from datetime import datetime

import httpx

from halo.config import get_settings
from halo.models import CreatorAccount
from halo.sources.base import AccountSnapshot, SourceError, SourceVideo

API = "https://www.googleapis.com/youtube/v3"
_DURATION = re.compile(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?")


def parse_duration(value: str) -> float | None:
    match = _DURATION.fullmatch(value or "")
    if not match or not any(match.groups()):
        return None
    days, hours, minutes, seconds = (int(g or 0) for g in match.groups())
    return float(days * 86400 + hours * 3600 + minutes * 60 + seconds)


def _int(value: str | None) -> int | None:
    return int(value) if value is not None else None


class YouTubeSource:
    def __init__(self, api_key: str | None = None, transport: httpx.AsyncBaseTransport | None = None):
        self.api_key = api_key or get_settings().youtube_api_key
        self.transport = transport

    async def fetch(self, account: CreatorAccount, limit: int = 12) -> AccountSnapshot:
        if not self.api_key:
            raise SourceError("HALO_YOUTUBE_API_KEY is not set")
        async with httpx.AsyncClient(base_url=API, timeout=30, transport=self.transport) as http:
            params = {"part": "snippet,statistics,contentDetails", "key": self.api_key}
            if account.external_id:
                params["id"] = account.external_id
            else:
                handle = account.handle if account.handle.startswith("@") else f"@{account.handle}"
                params["forHandle"] = handle
            channels = (await self._get(http, "/channels", params)).get("items", [])
            if not channels:
                raise SourceError(f"YouTube channel {account.handle} not found")
            channel = channels[0]
            uploads = channel["contentDetails"]["relatedPlaylists"]["uploads"]

            items = (
                await self._get(
                    http,
                    "/playlistItems",
                    {"part": "contentDetails", "playlistId": uploads, "maxResults": limit, "key": self.api_key},
                )
            ).get("items", [])
            ids = [item["contentDetails"]["videoId"] for item in items]
            videos = []
            if ids:
                details = await self._get(
                    http,
                    "/videos",
                    {"part": "snippet,statistics,contentDetails", "id": ",".join(ids), "key": self.api_key},
                )
                videos = [self._to_video(v) for v in details.get("items", [])]

        stats = channel.get("statistics", {})
        followers = None if stats.get("hiddenSubscriberCount") else _int(stats.get("subscriberCount"))
        return AccountSnapshot(external_id=channel["id"], followers=followers, videos=videos)

    @staticmethod
    async def _get(http: httpx.AsyncClient, path: str, params: dict) -> dict:
        resp = await http.get(path, params=params)
        if resp.status_code != 200:
            raise SourceError(f"YouTube API {path} returned {resp.status_code}: {resp.text[:300]}")
        return resp.json()

    @staticmethod
    def _to_video(item: dict) -> SourceVideo:
        vid = item["id"]
        snippet = item.get("snippet", {})
        stats = item.get("statistics", {})
        thumbs = snippet.get("thumbnails", {})
        best = next((thumbs[k]["url"] for k in ("maxres", "standard", "high") if k in thumbs), None)
        frame_urls = ([best] if best else []) + [f"https://i.ytimg.com/vi/{vid}/{i}.jpg" for i in (1, 2, 3)]
        posted = snippet.get("publishedAt")
        return SourceVideo(
            external_id=vid,
            url=f"https://www.youtube.com/watch?v={vid}",
            caption=f"{snippet.get('title', '')}\n\n{snippet.get('description', '')}".strip(),
            posted_at=datetime.fromisoformat(posted.replace("Z", "+00:00")) if posted else None,
            frame_urls=frame_urls,
            views=_int(stats.get("viewCount")),
            likes=_int(stats.get("likeCount")),
            comments=_int(stats.get("commentCount")),
            duration_s=parse_duration(item.get("contentDetails", {}).get("duration", "")),
        )
