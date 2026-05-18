FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl && rm -rf /var/lib/apt/lists/*
COPY backend/pyproject.toml ./backend/pyproject.toml
RUN cd backend && pip install -e ".[scraping,semantic,jobspy]" && python -m playwright install --with-deps chromium
COPY backend/app ./app
COPY worker/app ./worker_app

CMD ["python", "-m", "worker_app.worker"]
