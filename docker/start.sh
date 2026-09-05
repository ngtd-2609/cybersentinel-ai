#!/bin/sh
set -e

echo "Running database migrations..."

/app/.venv/bin/alembic upgrade head

if [ "${CYBERSENTINEL_DEMO_SEED_ENABLED:-false}" = "true" ]; then
  echo "Ensuring safe portfolio demo data exists..."
  /app/.venv/bin/python -m cybersentinel_ai.demo.seed
fi

echo "Starting API..."

exec /app/.venv/bin/uvicorn \
  cybersentinel_ai.api.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}"
