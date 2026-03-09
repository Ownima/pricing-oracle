"""Dockerfile for Pricing Oracle."""

FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen

COPY pricing_oracle/ ./pricing_oracle/

EXPOSE 8000 8001

CMD ["uvicorn", "pricing_oracle.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
