FROM python:3.13-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    UV_NO_CACHE=1

WORKDIR /app

RUN pip install uv

FROM base AS builder
COPY pyproject.toml ./

RUN uv pip install --system --no-cache --requirement pyproject.toml

FROM base AS production
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY ./app /app/app
COPY ./alembic.ini /app/alembic.ini
COPY ./migrations /app/migrations

CMD ["uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8080"]
