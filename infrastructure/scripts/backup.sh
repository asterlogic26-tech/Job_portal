#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKUP_DIR="$PROJECT_ROOT/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

mkdir -p "$BACKUP_DIR"

echo "==> Starting backup at $TIMESTAMP..."

# PostgreSQL dump
echo "==> Dumping PostgreSQL..."
docker compose -f "$PROJECT_ROOT/docker-compose.yml" exec -T postgres \
    pg_dump -U postgres job_agent \
    | gzip > "$BACKUP_DIR/postgres_$TIMESTAMP.sql.gz"
echo "    Saved: backups/postgres_$TIMESTAMP.sql.gz"

# Qdrant snapshot (via API)
echo "==> Creating Qdrant snapshot..."
curl -s -X POST "http://localhost:6333/snapshots" \
    -H "Content-Type: application/json" \
    -o /dev/null && echo "    Qdrant snapshot created (check Qdrant UI)."

# MinIO sync (if mc is available)
if command -v mc &>/dev/null; then
    echo "==> Syncing MinIO to backup directory..."
    mc alias set local http://localhost:9000 "${MINIO_ROOT_USER:-minio}" "${MINIO_ROOT_PASSWORD:-minio_password}" 2>/dev/null || true
    mc mirror local/resumes "$BACKUP_DIR/minio_resumes_$TIMESTAMP/" 2>/dev/null || echo "    MinIO sync skipped (bucket may be empty)."
fi

# Prune old backups (keep last 7)
echo "==> Pruning old backups (keeping last 7)..."
ls -tp "$BACKUP_DIR"/postgres_*.sql.gz 2>/dev/null | tail -n +8 | xargs -r rm --

echo "==> Backup complete: $BACKUP_DIR"
