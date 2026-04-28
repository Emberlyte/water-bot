FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY pyproject.toml uv.lock ./


RUN uv pip install --system -r pyproject.toml

RUN mkdir -p /app/data

COPY . .

CMD ["python", "main.py"]