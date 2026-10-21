"""Halo as one service: the API under /api and the built web app at /.

Docker Compose runs the API, worker and web server as separate containers. Hosts that give
one free service (Render, see render.yaml and the root Dockerfile) run this app instead, with
HALO_JOBS=inline so background jobs run in this process, and HALO_ACCESS_PASSWORD set.

    uvicorn halo.api.site:site
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from halo import queue
from halo.api.auth import PasswordGate
from halo.api.main import app as api
from halo.config import get_settings
from halo.logs import show_halo_logs


@asynccontextmanager
async def lifespan(app: FastAPI):
    # A mounted app gets no lifespan events of its own, so do the API's work here.
    show_halo_logs()
    yield
    await queue.close()


def create_site() -> FastAPI:
    settings = get_settings()
    site = FastAPI(title="Halo", lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    site.mount("/api", api)
    if settings.web_dist and Path(settings.web_dist).is_dir():
        site.mount("/", StaticFiles(directory=settings.web_dist, html=True), name="web")
    if settings.access_password:
        # The host's health check has no password, and only learns that the app is up.
        site.add_middleware(PasswordGate, password=settings.access_password, open_paths=frozenset({"/api/health"}))
    return site


site = create_site()
