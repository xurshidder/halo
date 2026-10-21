"""One-service hosting: database URLs from hosts, the site app, its password, inline jobs, demo seed."""

import asyncio
import base64

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select

from halo import queue, worker
from halo.config import Settings, get_settings
from halo.models import Brand
from scripts import seed_demo


@pytest.mark.parametrize(
    ("given", "expected"),
    [
        # Neon's connection string, as its console shows it
        (
            "postgresql://halo_owner:pw@ep-cool-1.eu-central-1.aws.neon.tech/halo?sslmode=require&channel_binding=require",
            "postgresql+asyncpg://halo_owner:pw@ep-cool-1.eu-central-1.aws.neon.tech/halo?ssl=require",
        ),
        ("postgres://u:pw@db.example.com:5432/halo", "postgresql+asyncpg://u:pw@db.example.com:5432/halo"),
        # Already in Halo's own form: left exactly as it is
        ("postgresql+asyncpg://postgres@/halo?host=/tmp&port=5433", "postgresql+asyncpg://postgres@/halo?host=/tmp&port=5433"),
    ],
)
def test_database_urls_from_hosts_work_with_asyncpg(given, expected):
    assert Settings(database_url=given).database_url == expected


@pytest.fixture
def settings_env(monkeypatch):
    """Set HALO_* variables for one test, with fresh settings before and after."""

    def apply(**values):
        for key, value in values.items():
            monkeypatch.setenv(f"HALO_{key.upper()}", value)
        get_settings.cache_clear()

    yield apply
    monkeypatch.undo()
    get_settings.cache_clear()


def basic(password: str, user: str = "team") -> dict:
    return {"Authorization": "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode()}


async def test_site_serves_web_and_api_behind_the_password(settings_env, tmp_path):
    (tmp_path / "index.html").write_text("<h1>Halo web</h1>")
    settings_env(web_dist=str(tmp_path), access_password="olma-123")
    from halo.api.site import create_site

    async with AsyncClient(transport=ASGITransport(app=create_site()), base_url="http://test") as client:
        locked = await client.get("/")
        assert locked.status_code == 401
        assert locked.headers["www-authenticate"].startswith("Basic")
        assert (await client.get("/", headers=basic("wrong"))).status_code == 401

        page = await client.get("/", headers=basic("olma-123"))
        assert page.status_code == 200 and "Halo web" in page.text
        brands = await client.get("/api/brands", headers=basic("olma-123", user="anyone"))
        assert brands.status_code == 200 and brands.json() == []

        assert (await client.get("/api/health")).json() == {"ok": True}  # the host's health check needs no password


async def test_site_without_password_is_open(settings_env):
    settings_env(web_dist="")
    from halo.api.site import create_site

    async with AsyncClient(transport=ASGITransport(app=create_site()), base_url="http://test") as client:
        assert (await client.get("/api/brands")).status_code == 200


async def test_inline_jobs_run_in_process_and_can_queue_more(settings_env, monkeypatch, caplog):
    settings_env(jobs="inline")
    ran = []

    async def first_task(ctx, n):
        ran.append(("first", n))
        await ctx["redis"].enqueue_job("second_task", n + 1)

    async def second_task(ctx, n):
        ran.append(("second", n))

    async def broken_task(ctx):
        raise RuntimeError("boom")

    monkeypatch.setattr(worker.WorkerSettings, "functions", [first_task, second_task, broken_task])

    await queue.JobQueue().enqueue("first_task", 1)
    await queue.JobQueue().enqueue("broken_task")
    while queue._inline:
        await asyncio.gather(*list(queue._inline))

    assert ran == [("first", 1), ("second", 2)]
    assert "Background job broken_task() failed" in caplog.text  # logged, not raised into the API


async def test_demo_seed_if_empty_loads_once(session):
    await seed_demo.main(if_empty=True)
    await seed_demo.main(if_empty=True)
    assert await session.scalar(select(func.count()).select_from(Brand)) == 1
