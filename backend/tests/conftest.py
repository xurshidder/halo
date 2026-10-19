import os
import subprocess
import tempfile
from pathlib import Path

# Point settings at the test database before any halo module reads them.
os.environ.setdefault("HALO_DATABASE_URL", "postgresql+asyncpg://postgres@/halo_test?host=/tmp&port=5433")
os.environ["HALO_MEDIA_DIR"] = tempfile.mkdtemp(prefix="halo-media-")
for key in (
    "HALO_ANTHROPIC_API_KEY", "HALO_VOYAGE_API_KEY", "HALO_ELEVENLABS_API_KEY", "HALO_TELEGRAM_BOT_TOKEN",
    "HALO_YOUTUBE_API_KEY",
):
    os.environ.pop(key, None)

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from halo.ai import claude
from halo.api.main import app
from halo.db import get_engine, get_sessionmaker
from halo.models import Base
from halo.queue import get_queue


@pytest.fixture(scope="session", autouse=True)
async def schema():
    async with get_engine().begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    await get_engine().dispose()


@pytest.fixture(autouse=True)
async def clean_tables():
    yield
    names = ", ".join(t.name for t in reversed(Base.metadata.sorted_tables))
    async with get_engine().begin() as conn:
        await conn.execute(text(f"TRUNCATE {names} RESTART IDENTITY CASCADE"))


@pytest.fixture
async def session():
    async with get_sessionmaker()() as s:
        yield s


class FakeClaude:
    """Stands in for halo.ai.claude.parse. Register a responder per output type."""

    def __init__(self):
        self.responders = {}
        self.calls = []

    def on(self, output_type, responder):
        self.responders[output_type] = responder

    async def parse(self, output_type, *, system, content, effort, max_tokens=16000):
        self.calls.append({"type": output_type, "system": system, "content": content, "effort": effort})
        responder = self.responders[output_type]
        return responder(content) if callable(responder) else responder


@pytest.fixture
def fake_claude(monkeypatch):
    fake = FakeClaude()
    monkeypatch.setattr(claude, "parse", fake.parse)
    return fake


class FakeQueue:
    def __init__(self):
        self.jobs = []

    async def enqueue(self, function, *args):
        self.jobs.append((function, *args))


@pytest.fixture
def jobs():
    queue = FakeQueue()
    app.dependency_overrides[get_queue] = lambda: queue
    yield queue
    app.dependency_overrides.pop(get_queue, None)


@pytest.fixture
async def api(jobs):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.fixture(scope="session")
def sample_video() -> Path:
    """A 6-second 640x360 test video with a tone, made with ffmpeg."""
    path = Path(tempfile.mkdtemp()) / "sample.mp4"
    subprocess.run(
        [
            "ffmpeg", "-v", "error", "-y",
            "-f", "lavfi", "-i", "testsrc=duration=6:size=640x360:rate=25",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=6",
            "-shortest", "-pix_fmt", "yuv420p", str(path),
        ],
        check=True,
    )
    return path
