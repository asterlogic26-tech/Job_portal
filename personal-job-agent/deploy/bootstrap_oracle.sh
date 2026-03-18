#!/bin/bash
# =============================================================================
# bootstrap_oracle.sh — One-time Oracle Cloud Ampere A1 setup
#
# Key differences from EC2:
#   1. Oracle Ubuntu has TWO firewalls: VCN Security List + OS iptables.
#      Both must allow ports 80 and 443 — this script handles the OS layer.
#   2. Uses netfilter-persistent so rules survive reboots.
#   3. Swap is pre-configured (24 GB RAM — enough without swap, but we add
#      2 GB as safety for model loading spikes).
#
# Run as ubuntu on a fresh Oracle Ubuntu 22.04 instance:
#   bash deploy/bootstrap_oracle.sh
# =============================================================================
set -euo pipefail

echo "============================================"
echo " Personal AI Job Agent — Oracle Cloud Setup"
echo " ARM64 (Ampere A1) · Ubuntu 22.04"
echo "============================================"

# ── 1. System update ──────────────────────────────────────────────────────────
sudo apt-get update -y
sudo apt-get upgrade -y
sudo apt-get install -y \
  curl git vim htop unzip \
  ca-certificates gnupg lsb-release \
  iptables-persistent netfilter-persistent \
  fail2ban dig

# ── 2. CRITICAL: Oracle OS-level firewall ────────────────────────────────────
# Oracle Ubuntu blocks ports 80/443 via iptables even if the VCN Security List
# allows them. These rules MUST be added or nginx will not be reachable.
echo "Configuring OS firewall (iptables)..."

sudo iptables  -I INPUT 6 -m state --state NEW -p tcp --dport 80  -j ACCEPT
sudo iptables  -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo ip6tables -I INPUT 6 -m state --state NEW -p tcp --dport 80  -j ACCEPT
sudo ip6tables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT

# Save rules so they survive reboots
sudo netfilter-persistent save
echo "Firewall rules saved."

# ── 3. Kernel network tuning (better throughput) ──────────────────────────────
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

# ── 4. Small swap (safety buffer for model loading spikes) ───────────────────
if [ ! -f /swapfile ]; then
  echo "Creating 2 GB swap..."
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
  sudo install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  sudo chmod a+r /etc/apt/keyrings/docker.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
    https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" \
    | sudo tee /etc/apt/sources.list.d/docker.list
  sudo apt-get update -y
  sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
  sudo systemctl enable docker
  sudo systemctl start docker
  sudo usermod -aG docker ubuntu
fi

echo "Docker: $(docker --version)"
echo "Compose: $(docker compose version)"

# ── 6. Deploy directory ───────────────────────────────────────────────────────
sudo mkdir -p /opt/personal-job-agent
sudo chown ubuntu:ubuntu /opt/personal-job-agent

# ── 7. Fail2ban ───────────────────────────────────────────────────────────────
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# ── 8. Aliases ────────────────────────────────────────────────────────────────
cat >> ~/.bashrc <<'EOF'

# Job Agent shortcuts
APP=/opt/personal-job-agent
alias dc="docker compose -f $APP/docker-compose.yml -f $APP/docker-compose.prod.yml -f $APP/docker-compose.oracle.yml"
alias dclogs="dc logs -f --tail=50"
alias dcps="dc ps"
alias dcrestart="dc restart"
alias usage="curl -s http://localhost:8000/api/v1/agents/limits | python3 -m json.tool"
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
