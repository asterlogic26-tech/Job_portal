#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

echo "==> Starting Personal Job Agent..."

# Check .env exists
if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found. Copy .env.example to .env and fill in your API keys."
    exit 1
fi

# Pull latest images
echo "==> Pulling Docker images..."
docker compose pull --quiet

# Build application images
echo "==> Building application images..."
docker compose build --parallel

# Start infrastructure services first
echo "==> Starting infrastructure services..."
docker compose up -d postgres redis qdrant minio

# Wait for Postgres
echo "==> Waiting for PostgreSQL..."
until docker compose exec -T postgres pg_isready -U postgres -q; do
    sleep 2
done
echo "    PostgreSQL ready."

# Run migrations
echo "==> Running database migrations..."
docker compose run --rm backend alembic upgrade head

# Seed data (idempotent)
echo "==> Seeding initial data..."
docker compose run --rm backend python -c "
from backend.db.init_db import run_seed
import asyncio
asyncio.run(run_seed())
"

# Start all remaining services
echo "==> Starting all services..."
docker compose up -d

echo ""
echo "==> Personal Job Agent is running!"
echo "    Dashboard:  http://localhost"
echo "    API docs:   http://localhost/api/docs"
echo "    Flower:     http://localhost:5555"
echo "    MinIO UI:   http://localhost:9001"
echo ""
echo "Run 'docker compose logs -f' to watch logs."
