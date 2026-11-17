# syntax=docker/dockerfile:1
ARG PYTHON_IMAGE=python:3.12-slim
ARG UV_IMAGE=ghcr.io/astral-sh/uv:0.8.5
FROM ${UV_IMAGE} AS uv
FROM ${PYTHON_IMAGE} AS builder
COPY --from=uv /uv /bin/uv
WORKDIR /app
ENV UV_PROJECT_ENVIRONMENT=/app/.venv UV_LINK_MODE=copy
RUN apt-get update && apt-get install -y --no-install-recommends build-essential pkg-config default-libmysqlclient-dev libffi-dev && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev --no-install-project

FROM ${PYTHON_IMAGE} AS runtime-base
RUN apt-get update && apt-get install -y --no-install-recommends libmariadb3 libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 fonts-dejavu-core && rm -rf /var/lib/apt/lists/*
COPY --from=uv /uv /bin/uv
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 UV_PROJECT_ENVIRONMENT=/app/.venv UV_NO_SYNC=1 UV_NO_CACHE=1 UV_PYTHON_DOWNLOADS=never MALLOC_ARENA_MAX=2 APP_PORT=8005 PATH="/app/.venv/bin:$PATH"

FROM runtime-base AS assets
COPY --from=builder /app/.venv /app/.venv
COPY . .
RUN mkdir -p /app/logs && DEBUG=true WRITE_LOG_ON_FILE=false DB_ENGINE=sqlite3 DB_NAME=:memory: STATIC_ROOT=/static_cdn uv run python manage.py collectstatic --noinput && chmod +x ./start.sh

FROM runtime-base AS runtime
RUN groupadd --gid 10001 app && useradd --uid 10001 --gid app --no-create-home app
COPY --from=assets /app /app
COPY --from=assets /static_cdn /static_cdn
USER 10001:10001
EXPOSE 8005
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=5 CMD ["/app/.venv/bin/python", "/app/wma/healthcheck.py"]
CMD ["sh", "-c", "exec ./start.sh --prod --host 0.0.0.0 --port \"$APP_PORT\" --workers 1 --check --check-migrations"]
