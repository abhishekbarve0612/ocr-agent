# syntax=docker/dockerfile:1
ARG PYTHON_VERSION=3.13
FROM python:${PYTHON_VERSION}-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VERSION=1.8.3 \
    POETRY_VIRTUALENVS_CREATE=false \
    PORT=8000 \
    PATH="/root/.local/bin:$PATH"

WORKDIR /app

# System deps (only what you need; add libpq-dev if using Postgres)
# - tesseract-ocr and tesseract-ocr-eng are required for pytesseract to work
# - image libs help Pillow handle common formats without compiling
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    tesseract-ocr \
    tesseract-ocr-eng \
    libjpeg62-turbo \
    libpng16-16 \
    zlib1g \
  && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install "poetry==$POETRY_VERSION"

# Copy only dependency files first (for better Docker layer caching)
COPY pyproject.toml poetry.lock* ./

# Install deps (main only; skip dev)
RUN poetry install --no-root --only main

# Ensure Gunicorn is available (it's used as the entrypoint)
RUN pip install gunicorn

# Now copy app code
COPY . .

# Note: collectstatic is intentionally omitted here because STATIC_ROOT is not
# configured in settings. Run it at deploy/runtime once STATIC_ROOT is set.

# Make port available
EXPOSE 8000

# Gunicorn entrypoint
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "60"]
