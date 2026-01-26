#!/bin/bash
# -----------------------------------------------------------------------------
# AI Receptionist - Unified Deployment Script
# -----------------------------------------------------------------------------
# This script syncs local changes to the production servers (Innovation and droplet)
# and restarts the services to apply updates.
# -----------------------------------------------------------------------------

set -e

# Configuration
BACKEND_HOST="Innovation"
BACKEND_DIR="/opt/ai-receptionist"
FRONTEND_HOST="droplet"
FRONTEND_DIR="/srv/ai_receptionist/dashboard_nextjs"

echo "🚀 Starting Deployment of AI Receptionist fixes..."

# 1. Sync Backend Code to Innovation Server
echo "📡 Syncing Backend to $BACKEND_HOST..."
# Using rsync to efficiently update the ai_receptionist folder and migrations
rsync -avz --exclude '.git' --exclude '__pycache__' --exclude 'node_modules' \
    ./backend/ $BACKEND_HOST:$BACKEND_DIR/

# 2. Restart Backend Service (Zero-Downtime Rolling Deployment)
echo "🔄 Restarting Backend Service on $BACKEND_HOST..."
# Reverting to standard restart to avoid port binding conflicts with rolling updates
ssh $BACKEND_HOST "cd $BACKEND_DIR && docker compose -f docker-compose.prod.yml up -d --build --force-recreate app"

# 3. Run Database Migrations on Backend
echo "🗄️ Running Database Migrations on $BACKEND_HOST..."
# Running alembic upgrade head inside the app container
ssh $BACKEND_HOST "cd $BACKEND_DIR && docker compose -f docker-compose.prod.yml exec -T -e PYTHONPATH=/app app alembic upgrade head"

# 4. Sync Frontend Code to droplet Server
echo "📡 Syncing Dashboard Frontend Files to $FRONTEND_HOST..."
# Sync app and lib directories specifically, plus package definition
rsync -avz --exclude 'node_modules' --exclude '.next' \
    ./frontend/package.json ./frontend/package-lock.json $FRONTEND_HOST:$FRONTEND_DIR/
rsync -avz --exclude 'node_modules' --exclude '.next' \
    ./frontend/app/ $FRONTEND_HOST:$FRONTEND_DIR/src/app/
rsync -avz \
    ./frontend/lib/ $FRONTEND_HOST:$FRONTEND_DIR/src/lib/

# 5. Restart Frontend Service (Rebuild to apply changes)
echo "🔄 Rebuilding and Restarting Frontend Service on $FRONTEND_HOST..."
ssh $FRONTEND_HOST "cd $FRONTEND_DIR && docker compose up -d --build"

echo ""
echo "✨ Deployment Complete!"
echo "📡 Backend URL: https://receptionist.lexmakesit.com/health"
echo "🌐 Dashboard URL: https://dashboard.lexmakesit.com/app/onboarding"
echo "-----------------------------------------------------------------------------"
