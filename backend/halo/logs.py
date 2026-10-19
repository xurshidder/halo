import logging


def show_halo_logs() -> None:
    """Print Halo's INFO lines (job progress, the token usage of every Claude call).

    arq and uvicorn only configure their own loggers, so without this they are dropped.
    """
    halo_log = logging.getLogger("halo")
    if halo_log.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s: %(name)s %(message)s", "%H:%M:%S"))
    halo_log.addHandler(handler)
    halo_log.setLevel(logging.INFO)
    halo_log.propagate = False
