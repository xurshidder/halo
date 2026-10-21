#!/bin/sh
# Start Halo as one service (root Dockerfile, render.yaml): migrate, optionally load the
# demo data into an empty database, then serve the web app and API on the host's $PORT.
set -e
alembic upgrade head
if [ -n "$HALO_SEED_DEMO" ]; then
  python -m scripts.seed_demo --if-empty
fi
exec uvicorn halo.api.site:site --host 0.0.0.0 --port "${PORT:-8000}"
