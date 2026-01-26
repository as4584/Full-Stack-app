#!/bin/bash

set -e  # Exit on any error

echo "🚀 Deploying Frontend to Production..."
echo "================================================"

# Configuration
FRONTEND_DIR="/home/lex/lexmakesit/frontend"
REMOTE_USER="root"
REMOTE_HOST="droplet"
REMOTE_PATH="/srv/ai_receptionist/dashboard_nextjs"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Clean and rebuild
echo -e "${YELLOW}Step 1: Building production bundle...${NC}"
cd "$FRONTEND_DIR"

# Remove old build
rm -rf .next

# Build for production
echo "Running: npm run build"
NODE_ENV=production npm run build

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Build failed! Aborting deployment.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Build successful${NC}"

# Step 2: Stop current container
echo -e "${YELLOW}Step 2: Stopping current container...${NC}"
ssh "$REMOTE_HOST" "docker stop dashboard_nextjs 2>/dev/null || true"
ssh "$REMOTE_HOST" "docker rm dashboard_nextjs 2>/dev/null || true"

# Step 3: Sync files
echo -e "${YELLOW}Step 3: Syncing files to production...${NC}"
rsync -avz --delete \
    --exclude 'node_modules' \
    --exclude '.git' \
    --exclude 'portfolio' \
    --exclude 'lexmakesit-infra' \
    --exclude '.next/cache' \
    "$FRONTEND_DIR/" "$REMOTE_HOST:$REMOTE_PATH/"

# Step 4: Build and start production container
echo -e "${YELLOW}Step 4: Starting production container...${NC}"
ssh "$REMOTE_HOST" "cd $REMOTE_PATH && docker compose -f docker-compose.prod.yml up -d --build"

# Step 5: Wait for container to be healthy
echo -e "${YELLOW}Step 5: Waiting for container to be healthy...${NC}"
sleep 10

# Check if container is running
CONTAINER_STATUS=$(ssh "$REMOTE_HOST" "docker ps --filter name=dashboard_nextjs_prod --format '{{.Status}}'")
if [ -z "$CONTAINER_STATUS" ]; then
    echo -e "${RED}❌ Container failed to start!${NC}"
    echo "Checking logs:"
    ssh "$REMOTE_HOST" "docker logs dashboard_nextjs_prod"
    exit 1
fi

echo -e "${GREEN}✅ Container is running${NC}"

# Step 6: Health check
echo -e "${YELLOW}Step 6: Running health check...${NC}"
sleep 5  # Give it time to fully start

HEALTH_CHECK=$(ssh "$REMOTE_HOST" "curl -s -o /dev/null -w '%{http_code}' http://localhost:3000/" || echo "000")

if [ "$HEALTH_CHECK" == "200" ] || [ "$HEALTH_CHECK" == "307" ]; then
    echo -e "${GREEN}✅ Health check passed (HTTP $HEALTH_CHECK)${NC}"
else
    echo -e "${RED}❌ Health check failed (HTTP $HEALTH_CHECK)${NC}"
    echo "Checking logs:"
    ssh "$REMOTE_HOST" "docker logs dashboard_nextjs_prod | tail -50"
    exit 1
fi

# Step 7: Verify no dev warnings
echo -e "${YELLOW}Step 7: Verifying production mode...${NC}"
ssh "$REMOTE_HOST" "docker exec dashboard_nextjs_prod env | grep NODE_ENV"

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}✅ Frontend deployed successfully!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "Dashboard URL: https://dashboard.lexmakesit.com"
echo "Container: dashboard_nextjs_prod"
echo ""
echo "View logs:"
echo "  ssh $REMOTE_HOST 'docker logs -f dashboard_nextjs_prod'"
echo ""
