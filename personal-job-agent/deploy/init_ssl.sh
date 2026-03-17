#!/bin/bash
# =============================================================================
# init_ssl.sh — One-time SSL certificate setup with Let's Encrypt
#
# Run AFTER:
#   - Your domain DNS is pointing to this server (A record)
#   - Ports 80 and 443 are open in AWS Security Group
#
# Usage: bash deploy/init_ssl.sh
# =============================================================================
set -euo pipefail

DOMAIN="networknimble.info"
EMAIL="${SSL_EMAIL:-admin@networknimble.info}"  # change via SSL_EMAIL env var
APP_DIR="${APP_DIR:-/opt/personal-job-agent}"

cd "$APP_DIR"

echo "================================================"
echo " SSL Certificate Setup for $DOMAIN"
echo "================================================"

# Verify domain is pointing here
SERVER_IP=$(curl -s https://api.ipify.org)
DOMAIN_IP=$(dig +short "$DOMAIN" @8.8.8.8 | tail -1)

if [ "$SERVER_IP" != "$DOMAIN_IP" ]; then
  echo ""
  echo "WARNING: $DOMAIN resolves to $DOMAIN_IP but this server is $SERVER_IP"
  echo "DNS may not have propagated yet. Continue anyway? (y/N)"
  read -r ans
  [[ "$ans" == "y" || "$ans" == "Y" ]] || exit 1
fi

# ── Step 1: Start nginx with HTTP-only config (for ACME challenge) ────────────
echo ""
echo "Step 1: Starting nginx in HTTP-only mode..."

# Temporarily use a minimal HTTP-only nginx config
docker run --rm -d \
  --name nginx_temp \
  -p 80:80 \
  -v "$APP_DIR/infrastructure/nginx":/etc/nginx/conf.d:ro \
  -v certbot_webroot:/var/www/certbot \
  nginx:1.25-alpine || true

# ── Step 2: Create volume directories ────────────────────────────────────────
docker volume create certbot_webroot 2>/dev/null || true
docker volume create letsencrypt 2>/dev/null || true

# ── Step 3: Run certbot to obtain certificate ─────────────────────────────────
echo ""
echo "Step 2: Obtaining Let's Encrypt certificate..."

docker run --rm \
  -v certbot_webroot:/var/www/certbot \
  -v letsencrypt:/etc/letsencrypt \
  certbot/certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    -d "$DOMAIN" \
    -d "www.$DOMAIN"

# ── Step 4: Download recommended SSL parameters ───────────────────────────────
echo ""
echo "Step 3: Downloading recommended SSL parameters..."

LETSENCRYPT_DIR=$(docker volume inspect letsencrypt --format '{{ .Mountpoint }}')
if [ ! -f "$LETSENCRYPT_DIR/options-ssl-nginx.conf" ]; then
  curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf \
    -o "$LETSENCRYPT_DIR/options-ssl-nginx.conf"
fi
if [ ! -f "$LETSENCRYPT_DIR/ssl-dhparams.pem" ]; then
  curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem \
    -o "$LETSENCRYPT_DIR/ssl-dhparams.pem"
fi

# ── Step 5: Stop temp nginx ───────────────────────────────────────────────────
docker stop nginx_temp 2>/dev/null || true

echo ""
echo "================================================"
echo " SSL certificate obtained successfully!"
echo ""
echo " Certificate: $DOMAIN + www.$DOMAIN"
echo " Auto-renewal: handled by certbot container"
echo ""
echo " Now run: bash deploy/deploy.sh"
echo "================================================"
