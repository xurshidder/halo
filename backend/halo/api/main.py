from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from halo import queue
from halo.api.routes import brands, briefs, creators
from halo.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
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


@app.get("/health")
async def health() -> dict:
    return {"ok": True}
