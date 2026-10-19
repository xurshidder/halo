import logging

import pytest

from halo.worker import WorkerSettings


@pytest.fixture
def halo_logger():
    logger = logging.getLogger("halo")
    saved = (list(logger.handlers), logger.level, logger.propagate)
    yield logger
    logger.handlers[:], logger.level, logger.propagate = saved


async def test_worker_startup_shows_halo_info_logs(halo_logger):
    # arq configures only its own logger, so Claude token usage lines would otherwise be dropped
    await WorkerSettings.on_startup({})
    assert halo_logger.isEnabledFor(logging.INFO)
    assert any(isinstance(h, logging.StreamHandler) for h in halo_logger.handlers)

    await WorkerSettings.on_startup({})  # a second call adds no duplicate handler
    assert len(halo_logger.handlers) == 1
