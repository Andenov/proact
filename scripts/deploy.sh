#!/bin/bash
# =============================================================
# PROACT Deploy — run this every time you want to update
# Usage: bash scripts/deploy.sh
# =============================================================
set -e

cd /opt/proact

echo ""
echo "======================================"
echo "  PROACT Deployment"
echo "======================================"
echo ""

# --- Check .env.production exists ---
if [ ! -f .env.production ]; then
    echo "ERROR: .env.production not found."
    echo "Run: cp .env.production.example .env.production"
    echo "Then fill in your values and retry."
    exit 1
fi

# --- Pull latest code ---
echo "[1/3] Pulling latest code..."
git pull origin master

# --- Build and start containers ---
echo "[2/3] Building and starting containers..."
docker compose -f docker-compose.prod.yml --env-file .env.production up --build -d

# --- Wait for API to be healthy ---
echo "[3/3] Waiting for API to be ready..."
sleep 10
for i in {1..12}; do
    if curl -sf http://localhost/api/health > /dev/null 2>&1; then
        echo "API is healthy."
        break
    fi
    echo "  Waiting... ($i/12)"
    sleep 5
done

# --- Show status ---
echo ""
docker compose -f docker-compose.prod.yml ps

SERVER_IP=$(curl -sf http://checkip.amazonaws.com 2>/dev/null || hostname -I | awk '{print $1}')

echo ""
echo "======================================"
echo "  Deployment complete!"
echo "======================================"
echo ""
echo "  Web:     http://$SERVER_IP"
echo "  API docs: http://$SERVER_IP/api/docs"
echo ""
echo "To view logs:  docker compose -f docker-compose.prod.yml logs -f"
echo "To stop:       docker compose -f docker-compose.prod.yml down"
echo ""
