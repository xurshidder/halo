"""Text embeddings for look-alike search, via Voyage AI.

Optional: without HALO_VOYAGE_API_KEY, Halo falls back to tag-overlap similarity.
"""

import math

import httpx

from halo.config import get_settings

VOYAGE_URL = "https://api.voyageai.com/v1/embeddings"


def enabled() -> bool:
    return bool(get_settings().voyage_api_key)


async def embed(texts: list[str], input_type: str = "document") -> list[list[float]] | None:
    settings = get_settings()
    if not settings.voyage_api_key or not texts:
        return None
    async with httpx.AsyncClient(timeout=60) as http:
        resp = await http.post(
            VOYAGE_URL,
            headers={"Authorization": f"Bearer {settings.voyage_api_key}"},
            json={
                "input": texts,
                "model": settings.voyage_model,
                "input_type": input_type,
                "output_dimension": settings.embedding_dim,
            },
        )
        resp.raise_for_status()
        data = sorted(resp.json()["data"], key=lambda d: d["index"])
        return [d["embedding"] for d in data]


def mean_vector(vectors: list[list[float]]) -> list[float] | None:
    vectors = [v for v in vectors if v is not None]
    if not vectors:
        return None
    dim = len(vectors[0])
    mean = [sum(v[i] for v in vectors) / len(vectors) for i in range(dim)]
    norm = math.sqrt(sum(x * x for x in mean)) or 1.0
    return [x / norm for x in mean]
