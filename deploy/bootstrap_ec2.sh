#!/bin/bash
# =============================================================================
# bootstrap_ec2.sh — One-time EC2 server setup
#
# Run as root (or with sudo) on a fresh Ubuntu 22.04 instance:
#   curl -fsSL https://raw.githubusercontent.com/<YOU>/<REPO>/main/deploy/bootstrap_ec2.sh | sudo bash
#
# Or after cloning:
#   sudo bash deploy/bootstrap_ec2.sh
# =============================================================================
set -euo pipefail

echo "============================================"
echo " Personal AI Job Agent — EC2 Bootstrap"
echo "============================================"

# ── 1. System update ──────────────────────────────────────────────────────────
apt-get update -y
apt-get upgrade -y
apt-get install -y \
  curl git vim htop unzip \
  ca-certificates gnupg lsb-release \
  ufw fail2ban

# ── 2. Swap space (2GB — prevents OOM when loading ML models) ─────────────────
if [ ! -f /swapfile ]; then
  echo "Creating 4GB swap..."
  fallocate -l 4G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
  sysctl vm.swappiness=10
  echo 'vm.swappiness=10' >> /etc/sysctl.conf
fi

# ── 3. Docker ─────────────────────────────────────────────────────────────────
if ! command -v docker &>/dev/null; then
  echo "Installing Docker..."
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
    https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
    > /etc/apt/sources.list.d/docker.list
  apt-get update -y
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
  systemctl enable docker
  systemctl start docker
  # Allow ubuntu user to run docker without sudo
  usermod -aG docker ubuntu || true
fi

echo "Docker version: $(docker --version)"
echo "Docker Compose version: $(docker compose version)"

# ── 4. Firewall ───────────────────────────────────────────────────────────────
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh          # port 22
ufw allow http         # port 80
ufw allow https        # port 443
ufw --force enable
echo "Firewall configured."

# ── 5. Deploy directory ───────────────────────────────────────────────────────
APP_DIR="/opt/personal-job-agent"
mkdir -p "$APP_DIR"
chown ubuntu:ubuntu "$APP_DIR"

# ── 6. Fail2ban (basic SSH brute-force protection) ────────────────────────────
systemctl enable fail2ban
systemctl start fail2ban

# ── 7. Useful aliases ─────────────────────────────────────────────────────────
cat >> /home/ubuntu/.bashrc <<'EOF'

# Job Agent shortcuts
alias dc="docker compose -f /opt/personal-job-agent/docker-compose.yml -f /opt/personal-job-agent/docker-compose.prod.yml"
alias dclogs="dc logs -f --tail=50"
alias dcrestart="dc restart"
EOF

echo ""
echo "============================================"
echo " Bootstrap complete!"
echo ""
echo " Next steps:"
echo "  1. cd /opt/personal-job-agent"
echo "  2. git clone <your-repo> ."
echo "  3. cp .env.example .env && nano .env"
echo "  4. bash deploy/init_ssl.sh"
echo "  5. bash deploy/deploy.sh"
echo "============================================"
