#!/bin/bash
# =============================================================================
# deploy.sh — Pull latest code and redeploy
#
# Called by: GitHub Actions CI/CD on every push to main
# Can also be run manually: bash deploy/deploy.sh
# Note: nginx runs on the HOST (not Docker) — managed separately
# =============================================================================
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/personal-job-agent}"
BRANCH="${DEPLOY_BRANCH:-main}"

cd "$APP_DIR"

# Auto-detect Docker Compose v1 vs v2
if docker compose version &>/dev/null 2>&1; then
  DC="docker compose"
else
  DC="docker-compose"
fi
COMPOSE="$DC -f docker-compose.yml"

echo "========================================"
echo " Deploying Personal AI Job Agent"
echo " $(date '+%Y-%m-%d %H:%M:%S')"
echo " Compose: $DC"
echo "========================================"

# ── 1. Pull latest code ───────────────────────────────────────────────────────
echo ""
echo "[1/5] Pulling latest code from $BRANCH..."
git fetch origin "$BRANCH"
git reset --hard "origin/$BRANCH"

# ── 2. Build changed images ───────────────────────────────────────────────────
echo ""
echo "[2/5] Building images..."
$COMPOSE build --no-cache backend worker frontend

# ── 3. Bring up infrastructure ────────────────────────────────────────────────
echo ""
echo "[3/5] Starting infrastructure..."
$COMPOSE up -d postgres redis qdrant minio

# Wait for postgres to be healthy
echo "Waiting for postgres..."
for i in $(seq 1 30); do
  $COMPOSE exec -T postgres pg_isready -U "${POSTGRES_USER:-postgres}" &>/dev/null && break
  sleep 2
done

# ── 4. Run migrations ─────────────────────────────────────────────────────────
echo ""
echo "[4/5] Running database migrations..."
$COMPOSE run --rm backend \
  sh -c "alembic -c backend/alembic.ini upgrade head"

# ── 5. Restart application services ──────────────────────────────────────────
echo ""
echo "[5/5] Restarting application services..."
$COMPOSE up -d backend worker celery-beat flower frontend

# Reload host nginx (nginx runs on host, not in Docker)
if systemctl is-active --quiet nginx; then
  echo "Reloading host nginx..."
  sudo systemctl reload nginx
fi

# ── Clean up ──────────────────────────────────────────────────────────────────
docker image prune -f

# ── Health check ─────────────────────────────────────────────────────────────
echo ""
echo "Checking backend health..."
sleep 10
STATUS=$(curl -sf -o /dev/null -w "%{http_code}" "http://localhost:8000/health" || echo "000")
if [ "$STATUS" = "200" ]; then
  echo "Backend is healthy (HTTP 200)"
else
  echo "WARNING: Backend returned HTTP $STATUS"
  echo "Check logs: $DC logs backend"
fi

echo ""
echo "========================================"
echo " Deploy complete!"
echo " Site: https://networknimble.info"
echo "========================================"
