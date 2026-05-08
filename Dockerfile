FROM python:3.14-alpine

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PYTHON_DOWNLOADS=never

RUN adduser -D appuser && chown appuser /app

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

COPY --chown=appuser:appuser . .

RUN mkdir -p /app/data && chown appuser /app/data

USER appuser

CMD ["/app/.venv/bin/python", "main.py"]
