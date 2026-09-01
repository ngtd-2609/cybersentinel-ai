#!/bin/sh
set -e

echo "Running database migrations..."

/app/.venv/bin/alembic upgrade head

echo "Starting API..."

exec /app/.venv/bin/uvicorn \
  cybersentinel_ai.api.main:app \
  --host 0.0.0.0 \
  --port 8000
