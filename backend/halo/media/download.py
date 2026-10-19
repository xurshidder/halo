import hashlib
from pathlib import Path

import httpx

from halo.config import get_settings

MAX_DOWNLOAD_BYTES = 200 * 1024 * 1024


def media_dir() -> Path:
    path = Path(get_settings().media_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


async def download(url: str, suffix: str = ".mp4") -> Path:
    """Stream a remote file into the media folder, refusing anything over 200 MB."""
    name = hashlib.sha256(url.encode()).hexdigest()[:24] + suffix
    target = media_dir() / name
    if target.exists():
        return target
    tmp = target.with_suffix(target.suffix + ".part")
    size = 0
    async with httpx.AsyncClient(timeout=120, follow_redirects=True) as http:
        async with http.stream("GET", url) as resp:
            resp.raise_for_status()
            with tmp.open("wb") as f:
                async for chunk in resp.aiter_bytes():
                    size += len(chunk)
                    if size > MAX_DOWNLOAD_BYTES:
                        tmp.unlink(missing_ok=True)
                        raise ValueError(f"File at {url} is larger than {MAX_DOWNLOAD_BYTES} bytes")
                    f.write(chunk)
    tmp.rename(target)
    return target


async def fetch_bytes(url: str) -> bytes:
    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as http:
        resp = await http.get(url)
        resp.raise_for_status()
        return resp.content
