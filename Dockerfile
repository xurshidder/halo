# Halo as one container: the built web app, the API and background jobs in one process.
# For hosts that give a single free service (render.yaml); Docker Compose uses backend/ and web/.

FROM node:22-alpine AS web
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY web/ .
RUN npm run build

FROM python:3.13-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:0.11.32 /uv /bin/uv

WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY backend/ .
COPY --from=web /web/dist /app/web

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    HALO_JOBS=inline \
    HALO_WEB_DIST=/app/web
EXPOSE 8000
CMD ["sh", "scripts/start_site.sh"]
