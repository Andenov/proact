#!/bin/bash
# =============================================================
# PROACT Server Setup — run once on a fresh DigitalOcean droplet
# Usage: bash scripts/server-setup.sh
# =============================================================
set -e

echo ""
echo "======================================"
echo "  PROACT Server Setup"
echo "======================================"
echo ""

# --- System update ---
echo "[1/5] Updating system packages..."
apt-get update -y && apt-get upgrade -y

# --- Install Docker ---
echo "[2/5] Installing Docker..."
curl -fsSL https://get.docker.com | sh
systemctl enable docker
systemctl start docker

# --- Install Docker Compose plugin ---
echo "[3/5] Installing Docker Compose..."
apt-get install -y docker-compose-plugin

# Verify
docker --version
docker compose version

# --- Install Git ---
echo "[4/5] Installing Git..."
apt-get install -y git

# --- Create app directory and clone ---
echo "[5/5] Cloning PROACT repository..."
mkdir -p /opt/proact
cd /opt/proact

echo ""
echo "Enter your GitHub repository URL (e.g. https://github.com/Andenov/proact.git):"
read REPO_URL
git clone "$REPO_URL" .

# Create required data directories
mkdir -p /opt/proact/nginx/ssl

echo ""
echo "======================================"
echo "  Setup complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "  1. cd /opt/proact"
echo "  2. cp .env.production.example .env.production"
echo "  3. nano .env.production   (fill in your values)"
echo "  4. bash scripts/deploy.sh"
echo ""
