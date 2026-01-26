#!/bin/bash
set -e

echo "=== Docker Production Deployment ==="
echo ""

# Step 1: Sync source files (exclude build artifacts)
echo "Step 1: Syncing source files to server..."
rsync -avz --progress \
  --exclude 'node_modules' \
  --exclude '.next' \
  --exclude '.git' \
  --exclude 'portfolio' \
  --exclude 'lexmakesit-infra' \
  --exclude '.env.local' \
  /home/lex/lexmakesit/frontend/ \
  droplet:/srv/ai_receptionist/dashboard_src/

# Step 2: Stop old containers
echo ""
echo "Step 2: Stopping old containers..."
ssh droplet "cd /srv/ai_receptionist/dashboard_src && docker compose -f docker-compose.prod.yml down 2>/dev/null || true"

# Step 3: Build and start production container on server
echo ""
echo "Step 3: Building and starting production container on server..."
ssh droplet "cd /srv/ai_receptionist/dashboard_src && docker compose -f docker-compose.prod.yml up -d --build"

# Step 4: Health check
echo ""
echo "Step 4: Waiting for container to start..."
sleep 10

ssh droplet "curl -f http://localhost:3000/ > /dev/null 2>&1" && \
  echo "✅ Dashboard is running!" || \
  (echo "❌ Health check failed. Checking logs..."; ssh droplet "docker logs dashboard_nextjs_prod --tail 50"; exit 1)

echo ""
echo "✅ Deployment complete!"
echo "Dashboard running at http://receptionlist.ai:3000"
echo ""
echo "Verify NODE_ENV with: ssh droplet 'docker exec dashboard_nextjs_prod env | grep NODE_ENV'"
