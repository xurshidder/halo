from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from halo import queue
from halo.api.routes import brands, briefs, creators, translations
from halo.config import get_settings
from halo.logs import show_halo_logs


@asynccontextmanager
async def lifespan(app: FastAPI):
    show_halo_logs()  # translations call Claude from the API process
    yield
    await queue.close()


app = FastAPI(title="Halo API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(brands.router)
app.include_router(creators.router)
app.include_router(briefs.router)
app.include_router(translations.router)


@app.get("/health")
async def health() -> dict:
    return {"ok": True}
