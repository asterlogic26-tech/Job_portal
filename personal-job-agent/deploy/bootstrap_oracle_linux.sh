#!/bin/bash
# =============================================================================
# bootstrap_oracle_linux.sh — One-time setup for Oracle Linux 8/9 on ARM
#
# Key differences from Ubuntu bootstrap:
#   - Uses dnf instead of apt-get
#   - Uses firewalld instead of ufw/iptables
#   - Default user is opc (not ubuntu)
#   - Docker repo is different
#
# Run as opc on a fresh Oracle Linux instance:
#   bash deploy/bootstrap_oracle_linux.sh
# =============================================================================
set -euo pipefail

echo "============================================"
echo " Personal AI Job Agent — Oracle Linux Setup"
echo " ARM64 (Ampere A1) · Oracle Linux 8/9"
echo "============================================"

# ── 1. System update ──────────────────────────────────────────────────────────
sudo dnf update -y
sudo dnf install -y \
  curl git vim htop unzip \
  ca-certificates gnupg \
  bind-utils \
  fail2ban

# ── 2. CRITICAL: Open ports in firewalld ─────────────────────────────────────
# Oracle Linux uses firewalld. Must open 80 and 443 at OS level
# (VCN Security List alone is NOT enough).
echo "Opening ports 80 and 443 in firewalld..."
sudo systemctl enable --now firewalld

sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload

echo "Firewall status:"
sudo firewall-cmd --list-services

# ── 3. Kernel network tuning ──────────────────────────────────────────────────
sudo tee -a /etc/sysctl.conf <<'EOF'

# Network performance
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728
net.ipv4.tcp_rmem = 4096 87380 67108864
net.ipv4.tcp_wmem = 4096 65536 67108864
net.ipv4.tcp_congestion_control = bbr
net.core.default_qdisc = fq
EOF
sudo sysctl -p

# ── 4. Swap (safety buffer for model loading) ─────────────────────────────────
if [ ! -f /swapfile ]; then
  echo "Creating 2GB swap..."
  sudo fallocate -l 2G /swapfile
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile
  sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
  echo 'vm.swappiness=5' | sudo tee -a /etc/sysctl.conf
  sudo sysctl vm.swappiness=5
fi

# ── 5. Docker ─────────────────────────────────────────────────────────────────
if ! command -v docker &>/dev/null; then
  echo "Installing Docker..."
  sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
  sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
  sudo systemctl enable --now docker
  # Allow opc user to run docker without sudo
  sudo usermod -aG docker opc
fi

echo "Docker:  $(docker --version)"
echo "Compose: $(docker compose version)"

# ── 6. Deploy directory ───────────────────────────────────────────────────────
sudo mkdir -p /opt/personal-job-agent
sudo chown opc:opc /opt/personal-job-agent

# ── 7. Fail2ban ───────────────────────────────────────────────────────────────
sudo systemctl enable --now fail2ban

# ── 8. Aliases ────────────────────────────────────────────────────────────────
cat >> ~/.bashrc <<'EOF'

# Job Agent shortcuts
APP=/opt/personal-job-agent
alias dc="docker compose -f $APP/docker-compose.yml -f $APP/docker-compose.prod.yml -f $APP/docker-compose.oracle.yml"
alias dclogs="dc logs -f --tail=50"
alias dcps="dc ps"
alias dcrestart="dc restart"
EOF

echo ""
echo "============================================"
echo " Bootstrap complete!"
echo ""
echo " IMPORTANT: Log out and back in so Docker"
echo " group takes effect, then run:"
echo ""
echo "  cd /opt/personal-job-agent"
echo "  git clone <your-repo> ."
echo "  cp .env.example .env && nano .env"
echo "  bash deploy/init_ssl.sh"
echo "  bash deploy/deploy.sh"
echo "============================================"
