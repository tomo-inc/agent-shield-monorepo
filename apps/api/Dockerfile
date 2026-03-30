FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY app ./app
COPY alembic.ini ./
COPY alembic ./alembic

RUN pip install --no-cache-dir uv \
    && uv pip install --system .[dev]

EXPOSE 8000
