import math

from halo.services.lookalike import find_lookalikes
from tests.factories import make_creator

DIM = 1024


def unit(*weights: float) -> list[float]:
    vec = list(weights) + [0.0] * (DIM - len(weights))
    norm = math.sqrt(sum(x * x for x in vec))
    return [x / norm for x in vec]


async def test_embedding_lookalikes_rank_by_cosine(session):
    seed = await make_creator(session, "Malika", ["skincare"], embedding=unit(1, 0))
    await make_creator(session, "Near", ["skincare"], embedding=unit(0.9, 0.1))
    await make_creator(session, "Far", ["cars"], embedding=unit(0, 1))
    await make_creator(session, "Unsafe", ["skincare"], embedding=unit(1, 0), risk="high")

    results = await find_lookalikes(session, seed.id)

    assert [c.display_name for c, _ in results] == ["Near", "Far"]
    assert results[0][1] > 0.95


async def test_tag_fallback_without_embeddings(session):
    seed = await make_creator(session, "Malika", ["skincare", "beauty"])
    await make_creator(session, "Both", ["skincare", "beauty"])
    await make_creator(session, "One", ["skincare", "food"])
    await make_creator(session, "None", ["cars"])

    results = await find_lookalikes(session, seed.id)

    assert [c.display_name for c, _ in results] == ["Both", "One"]
