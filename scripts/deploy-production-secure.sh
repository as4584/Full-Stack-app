#!/bin/bash
set -e

echo "=== PRODUCTION DEPLOYMENT: dashboard.lexmakesit.com ==="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Sync files
echo -e "${YELLOW}[1/7] Syncing files to server...${NC}"
rsync -avz --progress \
  --exclude 'node_modules' \
  --exclude '.next' \
  --exclude '.git' \
  --exclude 'portfolio' \
  --exclude 'lexmakesit-infra' \
  --exclude '.env.local' \
  /home/lex/lexmakesit/frontend/ \
  droplet:/srv/ai_receptionist/dashboard_src/

# Step 2: Update Caddyfile (bind-mounted from host)
echo ""
echo -e "${YELLOW}[2/7] Updating Caddy configuration...${NC}"
scp /home/lex/lexmakesit/infra/caddy/Caddyfile.production droplet:/home/lex/antigravity_bundle/apps/Caddyfile

# Step 3: Stop old container
echo ""
echo -e "${YELLOW}[3/7] Stopping old container...${NC}"
ssh droplet "cd /srv/ai_receptionist/dashboard_src && docker compose -f docker-compose.prod.locked.yml down 2>/dev/null || true"

# Step 4: Build new container (with correct network)
echo ""
echo -e "${YELLOW}[4/7] Building production container...${NC}"
ssh droplet "cd /srv/ai_receptionist/dashboard_src && docker compose -f docker-compose.prod.locked.yml build"

# Step 5: Start container on shared network
echo ""
echo -e "${YELLOW}[5/7] Starting container on apps_antigravity_net...${NC}"
ssh droplet "cd /srv/ai_receptionist/dashboard_src && docker compose -f docker-compose.prod.locked.yml up -d"

# Step 6: Reload Caddy
echo ""
echo -e "${YELLOW}[6/7] Reloading Caddy configuration...${NC}"
ssh droplet "docker exec antigravity_caddy caddy reload --config /etc/caddy/Caddyfile"

# Step 7: Health checks
echo ""
echo -e "${YELLOW}[7/7] Running health checks...${NC}"
echo "Waiting 10 seconds for container startup..."
sleep 10

# Check container is running
if ssh droplet "docker ps | grep dashboard_nextjs_prod" > /dev/null; then
    echo -e "${GREEN}✓ Container is running${NC}"
else
    echo -e "${RED}✗ Container failed to start${NC}"
    ssh droplet "docker logs dashboard_nextjs_prod --tail 50"
    exit 1
fi

# Check NODE_ENV
NODE_ENV=$(ssh droplet "docker exec dashboard_nextjs_prod env | grep NODE_ENV | cut -d= -f2")
if [ "$NODE_ENV" = "production" ]; then
    echo -e "${GREEN}✓ NODE_ENV=production${NC}"
else
    echo -e "${RED}✗ NODE_ENV is not production (got: $NODE_ENV)${NC}"
    exit 1
fi

# Check internal connectivity
if ssh droplet "docker exec antigravity_caddy wget -q --spider --timeout=5 http://dashboard_nextjs_prod:3000/"; then
    echo -e "${GREEN}✓ Caddy can reach container internally${NC}"
else
    echo -e "${RED}✗ Caddy cannot reach container${NC}"
    exit 1
fi

# Check external port is NOT accessible
if timeout 5 bash -c "nc -zv 104.236.100.245 3000 2>&1" | grep -q "succeeded"; then
    echo -e "${RED}✗ WARNING: Port 3000 is still publicly accessible!${NC}"
    echo "Run: ssh droplet 'sudo ufw deny 3000'"
else
    echo -e "${GREEN}✓ Port 3000 is not publicly accessible${NC}"
fi

# Check HTTPS works
echo ""
echo "Testing HTTPS endpoint..."
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 https://dashboard.lexmakesit.com)
if [ "$RESPONSE" = "200" ] || [ "$RESPONSE" = "307" ] || [ "$RESPONSE" = "302" ]; then
    echo -e "${GREEN}✓ HTTPS returns $RESPONSE (success)${NC}"
else
    echo -e "${RED}✗ HTTPS returns $RESPONSE (expected 200/307/302)${NC}"
    echo "Response:"
    curl -I https://dashboard.lexmakesit.com
    exit 1
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ DEPLOYMENT COMPLETE${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Production URL: https://dashboard.lexmakesit.com"
echo "Container: dashboard_nextjs_prod"
echo "Network: apps_antigravity_net (shared with Caddy)"
echo "Port: 3000 (internal only)"
echo ""
echo "Next: Run smoke test"
echo "  ./scripts/smoke-test-production.sh"
