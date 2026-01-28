#!/bin/bash
# =============================================================================
# DEPLOY AUTH + DASHBOARD - Dual Next.js App Deployment
# =============================================================================
# Deploys both auth.lexmakesit.com and dashboard.lexmakesit.com
# as separate, isolated Next.js applications
# =============================================================================

set -e

DROPLET="droplet"

echo "==========================================="
echo "🚀 DEPLOYING AUTH + DASHBOARD APPS"
echo "==========================================="

# Step 1: Sync auth frontend to server
echo ""
echo "[1/6] Syncing auth frontend..."
rsync -avz --delete \
    --exclude 'node_modules' \
    --exclude '.next' \
    --exclude '.git' \
    -e ssh \
    /home/lex/lexmakesit/auth-frontend/ \
    $DROPLET:/srv/ai_receptionist/auth_src/

# Step 2: Sync dashboard frontend to server
echo ""
echo "[2/6] Syncing dashboard frontend..."
rsync -avz --delete \
    --exclude 'node_modules' \
    --exclude '.next' \
    --exclude '.git' \
    -e ssh \
    /home/lex/lexmakesit/frontend/ \
    $DROPLET:/srv/ai_receptionist/dashboard_src/

# Step 3: Sync Caddy config
echo ""
echo "[3/6] Syncing Caddy configuration..."
scp /home/lex/lexmakesit/infra/caddy/Caddyfile.production \
    $DROPLET:/etc/caddy/Caddyfile

# Step 4: Build and deploy auth app
echo ""
echo "[4/6] Building and deploying AUTH app..."
ssh $DROPLET "cd /srv/ai_receptionist/auth_src && \
    docker compose -f docker-compose.prod.yml down --remove-orphans || true && \
    docker compose -f docker-compose.prod.yml build --no-cache && \
    docker compose -f docker-compose.prod.yml up -d"

# Step 5: Build and deploy dashboard app
echo ""
echo "[5/6] Building and deploying DASHBOARD app..."
ssh $DROPLET "cd /srv/ai_receptionist/dashboard_src && \
    rm -rf .next && \
    docker compose -f docker-compose.prod.locked.yml down --remove-orphans || true && \
    docker compose -f docker-compose.prod.locked.yml build --no-cache && \
    docker compose -f docker-compose.prod.locked.yml up -d"

# Step 6: Reload Caddy
echo ""
echo "[6/6] Reloading Caddy..."
ssh $DROPLET "docker exec antigravity_caddy caddy reload --config /etc/caddy/Caddyfile --force"

# Wait for containers to start
echo ""
echo "⏳ Waiting 15 seconds for containers to start..."
sleep 15

# Run verification
echo ""
echo "==========================================="
echo "🔍 RUNNING VERIFICATION TESTS"
echo "==========================================="
/home/lex/lexmakesit/scripts/verify-auth-dashboard-separation.sh

echo ""
echo "==========================================="
echo "✅ DEPLOYMENT COMPLETE"
echo "==========================================="
echo ""
echo "Auth App:      https://auth.lexmakesit.com"
echo "Dashboard App: https://dashboard.lexmakesit.com"
echo ""
echo "Flow:"
echo "  1. User visits dashboard.lexmakesit.com"
echo "  2. If not authenticated → redirect to auth.lexmakesit.com/login"
echo "  3. User logs in → cookie set with domain=.lexmakesit.com"
echo "  4. User redirected to dashboard.lexmakesit.com"
echo "  5. Dashboard reads cookie → shows content"
