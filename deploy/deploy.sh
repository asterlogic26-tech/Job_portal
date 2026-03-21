#!/bin/bash
# =============================================================================
# deploy.sh — Pull latest code and redeploy
#
# Called by: GitHub Actions CI/CD on every push to main
# Can also be run manually: bash deploy/deploy.sh
#
# Production stack:
#   docker-compose.yml          — base services (dev defaults)
#   docker-compose.prod.yml     — prod overrides: built frontend, docker nginx,
#                                  certbot, no exposed DB/backend ports
# SSL certs live in Docker named volume "letsencrypt" (created by init_ssl.sh)
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
COMPOSE="$DC -f docker-compose.yml -f docker-compose.prod.yml"

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
$COMPOSE up -d backend worker celery-beat flower frontend nginx certbot

# ── Clean up ──────────────────────────────────────────────────────────────────
docker image prune -f

# ── Health check ─────────────────────────────────────────────────────────────
echo ""
echo "Checking backend health (via nginx)..."
sleep 15
STATUS=$(curl -sf -o /dev/null -w "%{http_code}" "https://networknimble.info/api/v1/health" || echo "000")
if [ "$STATUS" = "200" ]; then
  echo "Backend is healthy (HTTP 200)"
else
  echo "WARNING: Backend returned HTTP $STATUS — checking internal..."
  # Fallback: check via docker exec in case nginx is still warming up
  $COMPOSE exec -T backend curl -sf http://localhost:8000/health && echo "Backend internal OK" || echo "Backend internal also unhealthy"
  echo "Check logs: $DC logs backend"
  echo "Check nginx: $DC logs nginx"
fi

echo ""
echo "========================================"
echo " Deploy complete!"
echo " Site: https://networknimble.info"
echo "========================================"
