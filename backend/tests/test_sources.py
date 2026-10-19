import httpx

from halo.models import CreatorAccount
from halo.sources.instagram import InstagramSource
from halo.sources.youtube import YouTubeSource, parse_duration


def test_parse_duration():
    assert parse_duration("PT45S") == 45
    assert parse_duration("PT1M5S") == 65
    assert parse_duration("PT1H2M3S") == 3723
    assert parse_duration("") is None


async def test_youtube_fetch():
    def handler(request: httpx.Request) -> httpx.Response:
        path, params = request.url.path, request.url.params
        if path.endswith("/channels"):
            assert params["forHandle"] == "@malika"
            return httpx.Response(200, json={"items": [{
                "id": "UC123",
                "statistics": {"subscriberCount": "10000"},
                "contentDetails": {"relatedPlaylists": {"uploads": "UU123"}},
            }]})
        if path.endswith("/playlistItems"):
            return httpx.Response(200, json={"items": [{"contentDetails": {"videoId": "vid1"}}]})
        if path.endswith("/videos"):
            return httpx.Response(200, json={"items": [{
                "id": "vid1",
                "snippet": {"title": "Ertalabki parvarish", "description": "uz", "publishedAt": "2026-10-01T10:00:00Z",
                            "thumbnails": {"high": {"url": "https://i.ytimg.com/vi/vid1/hqdefault.jpg"}}},
                "statistics": {"viewCount": "5000", "likeCount": "400", "commentCount": "100"},
                "contentDetails": {"duration": "PT58S"},
            }]})
        return httpx.Response(404)

    source = YouTubeSource(api_key="test", transport=httpx.MockTransport(handler))
    snapshot = await source.fetch(CreatorAccount(platform="youtube", handle="malika"))

    assert snapshot.external_id == "UC123"
    assert snapshot.followers == 10000
    video = snapshot.videos[0]
    assert video.caption.startswith("Ertalabki parvarish")
    assert video.duration_s == 58
    assert video.media_url is None
    assert video.frame_urls[0].endswith("hqdefault.jpg") and len(video.frame_urls) == 4
    assert snapshot.avg_views == 5000
    assert snapshot.engagement_rate == 0.05


async def test_instagram_fetch_keeps_only_videos():
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/me"):
            return httpx.Response(200, json={"user_id": "17841", "username": "malika.uz", "followers_count": 20000})
        if path.endswith("/me/media"):
            return httpx.Response(200, json={"data": [
                {"id": "m1", "media_type": "VIDEO", "media_url": "https://cdn/x.mp4", "permalink": "https://ig/p/1",
                 "caption": "Salom", "timestamp": "2026-10-01T10:00:00+0000", "like_count": 900, "comments_count": 100},
                {"id": "m2", "media_type": "IMAGE", "media_url": "https://cdn/y.jpg"},
            ]})
        if path.endswith("/m1/insights"):
            return httpx.Response(200, json={"data": [{"name": "views", "values": [{"value": 12000}]}]})
        return httpx.Response(404)

    source = InstagramSource(transport=httpx.MockTransport(handler))
    account = CreatorAccount(platform="instagram", handle="malika.uz", access_token="tok")
    snapshot = await source.fetch(account)

    assert snapshot.followers == 20000
    assert [v.external_id for v in snapshot.videos] == ["m1"]
    assert snapshot.videos[0].media_url == "https://cdn/x.mp4"
    assert snapshot.videos[0].views == 12000
    assert snapshot.engagement_rate == 0.05
