#!/bin/bash
# =============================================================================
# deploy.sh — Pull latest code and redeploy with zero-downtime
#
# Called by: GitHub Actions CI/CD on every push to main
# Can also be run manually: bash deploy/deploy.sh
# =============================================================================
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/personal-job-agent}"
BRANCH="${DEPLOY_BRANCH:-main}"

cd "$APP_DIR"

# Auto-detect Oracle Cloud override file
COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod.yml"
if [ -f "docker-compose.oracle.yml" ]; then
  COMPOSE_FILES="$COMPOSE_FILES -f docker-compose.oracle.yml"
  echo "Oracle Cloud mode: using docker-compose.oracle.yml"
fi
COMPOSE="docker compose $COMPOSE_FILES"

echo "========================================"
echo " Deploying Personal AI Job Agent"
echo " $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"

# ── 1. Pull latest code ───────────────────────────────────────────────────────
echo ""
echo "[1/5] Pulling latest code from $BRANCH..."
git fetch origin "$BRANCH"
git reset --hard "origin/$BRANCH"

# ── 2. Build changed images ───────────────────────────────────────────────────
echo ""
echo "[2/5] Building images..."
$COMPOSE build --pull --no-cache backend worker frontend

# ── 3. Run migrations before restarting backend ───────────────────────────────
echo ""
echo "[3/5] Running database migrations..."
$COMPOSE run --rm backend \
  sh -c "alembic -c backend/alembic.ini upgrade head"

# ── 4. Restart services (rolling, infrastructure first) ──────────────────────
echo ""
echo "[4/5] Restarting services..."
# Infrastructure first (no rebuild needed)
$COMPOSE up -d postgres redis qdrant minio

# Wait for postgres to be healthy
echo "Waiting for postgres..."
for i in $(seq 1 30); do
  $COMPOSE exec -T postgres pg_isready -U "${POSTGRES_USER:-postgres}" &>/dev/null && break
  sleep 2
done

# Application services
$COMPOSE up -d backend worker celery-beat flower nginx certbot

# ── 5. Clean up ───────────────────────────────────────────────────────────────
echo ""
echo "[5/5] Cleaning up dangling images..."
docker image prune -f

# ── Health check ─────────────────────────────────────────────────────────────
echo ""
echo "Checking backend health..."
sleep 5
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/health" || echo "000")
if [ "$STATUS" = "200" ]; then
  echo "Backend is healthy (HTTP 200)"
else
  echo "WARNING: Backend returned HTTP $STATUS — check logs with: docker compose logs backend"
fi

echo ""
echo "========================================"
echo " Deploy complete!"
echo " Site: https://networknimble.info"
echo " API:  https://networknimble.info/docs"
echo " Flower: https://networknimble.info/flower"
echo "========================================"
