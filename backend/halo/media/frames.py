"""Sample frames and audio from a video file with ffmpeg.

Claude reads images, not video files, so each video becomes a handful of frames.
The first three seconds get extra frames because that is where the hook lives.
"""

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path


class MediaError(RuntimeError):
    pass


@dataclass
class Frame:
    timestamp_s: float
    jpeg: bytes


async def _run(*args: str) -> bytes:
    proc = await asyncio.create_subprocess_exec(
        *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise MediaError(f"{args[0]} failed: {stderr.decode(errors='replace')[-500:]}")
    return stdout


async def probe_duration(path: Path) -> float:
    out = await _run(
        "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)
    )
    try:
        return float(json.loads(out)["format"]["duration"])
    except (KeyError, ValueError, json.JSONDecodeError) as e:
        raise MediaError(f"Could not read duration of {path.name}") from e


MIN_FRAME_GAP_S = 0.5


def frame_timestamps(duration_s: float, count: int) -> list[float]:
    """Hook-weighted timestamps: three in the first 3 seconds, the rest spread over the video.

    Frames stay at least half a second apart, so very short clips get fewer frames.
    """
    if duration_s <= 0 or count <= 0:
        return []
    hook = [t for t in (0.3, 1.5, 3.0) if t < duration_s][: min(3, count)]
    start = hook[-1] if hook else 0.0
    end = duration_s * 0.97
    rest = min(count - len(hook), int((end - start) / MIN_FRAME_GAP_S))
    if rest <= 0:
        return hook
    step = (end - start) / rest
    return hook + [round(start + step * (i + 1), 2) for i in range(rest)]


async def extract_frames(path: Path, count: int, width: int) -> list[Frame]:
    duration = await probe_duration(path)
    frames = []
    for ts in frame_timestamps(duration, count):
        jpeg = await _run(
            "ffmpeg", "-v", "error", "-ss", f"{ts:.2f}", "-i", str(path),
            "-frames:v", "1", "-vf", f"scale={width}:-2", "-q:v", "4",
            "-f", "image2", "-c:v", "mjpeg", "pipe:1",
        )
        if jpeg:
            frames.append(Frame(timestamp_s=ts, jpeg=jpeg))
    if not frames:
        raise MediaError(f"No frames could be extracted from {path.name}")
    return frames


async def extract_audio(path: Path, max_seconds: int) -> bytes | None:
    """16 kHz mono MP3 of the soundtrack, or None when the video has no audio."""
    try:
        audio = await _run(
            "ffmpeg", "-v", "error", "-i", str(path), "-t", str(max_seconds),
            "-vn", "-ac", "1", "-ar", "16000", "-f", "mp3", "pipe:1",
        )
    except MediaError:
        return None
    return audio or None
