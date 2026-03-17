#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

echo "WARNING: This will destroy all data in your development environment."
read -rp "Type 'yes' to confirm: " confirm
[ "$confirm" != "yes" ] && echo "Aborted." && exit 0

echo "==> Stopping all services..."
docker compose down -v --remove-orphans

echo "==> Removing local data volumes..."
rm -rf data/postgres data/redis data/qdrant data/minio

echo "==> Removing cached Python bytecode..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

echo "==> Rebuilding images from scratch..."
docker compose build --no-cache --parallel

echo "==> Starting infrastructure..."
docker compose up -d postgres redis qdrant minio

echo "==> Waiting for PostgreSQL..."
until docker compose exec -T postgres pg_isready -U postgres -q; do
    sleep 2
done

echo "==> Running fresh migrations..."
docker compose run --rm backend alembic upgrade head

echo "==> Seeding data..."
docker compose run --rm backend python -c "
from backend.db.init_db import run_seed
import asyncio
asyncio.run(run_seed())
"

echo "==> Dev environment reset complete."
echo "    Run 'make up' or 'docker compose up' to start."
