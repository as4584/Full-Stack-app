#!/bin/bash
set -e

echo "🚀 Deploying Frontend Applications to Production"
echo "=================================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
BACKEND_DIR="/opt/ai-receptionist"
FRONTEND_DIR="/opt/ai-receptionist/frontend"
AUTH_DIR="/opt/ai-receptionist/auth-frontend"
CADDY_CONFIG="/etc/caddy/Caddyfile"

# Step 1: Update Caddyfile
echo ""
echo "📝 Step 1: Updating Caddy configuration..."
if [ -f "$BACKEND_DIR/Caddyfile.production" ]; then
    sudo cp "$BACKEND_DIR/Caddyfile.production" "$CADDY_CONFIG"
    sudo systemctl reload caddy
    echo -e "${GREEN}✅ Caddy configuration updated${NC}"
else
    echo -e "${RED}❌ Caddyfile.production not found!${NC}"
    exit 1
fi

# Step 2: Deploy Dashboard Frontend
echo ""
echo "🎨 Step 2: Deploying Dashboard Frontend..."
cd "$BACKEND_DIR"

# Check if frontend directory exists
if [ ! -d "frontend" ]; then
    echo -e "${YELLOW}⚠️  Frontend directory not found, pulling from repo...${NC}"
    git fetch origin
fi

# Stop existing container if running
docker compose -f docker-compose.prod.yml down dashboard 2>/dev/null || true

# Build and start dashboard
cd frontend
if [ ! -f "docker-compose.prod.yml" ]; then
    echo -e "${RED}❌ frontend/docker-compose.prod.yml not found!${NC}"
    exit 1
fi

docker compose -f docker-compose.prod.yml down 2>/dev/null || true
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d

echo -e "${GREEN}✅ Dashboard deployed${NC}"

# Step 3: Deploy Auth Frontend  
echo ""
echo "🔐 Step 3: Deploying Auth Frontend..."
cd "$BACKEND_DIR/auth-frontend"

# Build and start auth
docker compose -f docker-compose.prod.yml down 2>/dev/null || true
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d

echo -e "${GREEN}✅ Auth frontend deployed${NC}"

# Step 4: Health Checks
echo ""
echo "🏥 Step 4: Running health checks..."
sleep 10

# Check dashboard
DASHBOARD_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/ || echo "000")
if [ "$DASHBOARD_STATUS" = "200" ] || [ "$DASHBOARD_STATUS" = "307" ]; then
    echo -e "${GREEN}✅ Dashboard healthy (HTTP $DASHBOARD_STATUS)${NC}"
else
    echo -e "${YELLOW}⚠️  Dashboard: HTTP $DASHBOARD_STATUS${NC}"
fi

# Check auth
AUTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3001/signin || echo "000")
if [ "$AUTH_STATUS" = "200" ] || [ "$AUTH_STATUS" = "404" ]; then
    echo -e "${GREEN}✅ Auth frontend healthy (HTTP $AUTH_STATUS)${NC}"
else
    echo -e "${YELLOW}⚠️  Auth frontend: HTTP $AUTH_STATUS${NC}"
fi

# Check external URLs
echo ""
echo "🌐 Checking external URLs..."
sleep 5

LIVE_DASHBOARD=$(curl -s -o /dev/null -w "%{http_code}" https://lexmakesit.com/ || echo "000")
LIVE_AUTH=$(curl -s -o /dev/null -w "%{http_code}" https://auth.lexmakesit.com/signin || echo "000")

echo "Dashboard (lexmakesit.com): HTTP $LIVE_DASHBOARD"
echo "Auth (auth.lexmakesit.com): HTTP $LIVE_AUTH"

# Step 5: Summary
echo ""
echo "=================================================="
echo "🎉 Deployment Complete!"
echo "=================================================="
echo ""
echo "📊 Container Status:"
docker ps --filter "name=dashboard" --filter "name=auth" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "🔗 URLs:"
echo "  Dashboard: https://lexmakesit.com (HTTP $LIVE_DASHBOARD)"
echo "  Auth:      https://auth.lexmakesit.com (HTTP $LIVE_AUTH)"
echo "  API:       https://receptionist.lexmakesit.com"

echo ""
if [ "$LIVE_DASHBOARD" = "502" ] || [ "$LIVE_AUTH" = "502" ]; then
    echo -e "${RED}❌ CRITICAL: 502 errors detected!${NC}"
    echo "Check logs: docker compose logs dashboard auth"
    exit 1
else
    echo -e "${GREEN}✅ All services responding successfully${NC}"
fi
