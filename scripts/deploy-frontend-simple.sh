#!/bin/bash
set -e

echo "=== Simple Production Deployment (No Docker) ==="
echo ""

# Step 1: Build locally
echo "Step 1: Building production bundle locally..."
cd /home/lex/lexmakesit/frontend
NODE_ENV=production npm run build

# Step 2: Stop any running containers
echo ""
echo "Step 2: Stopping any running containers..."
ssh droplet "docker stop dashboard_nextjs 2>/dev/null || true"
ssh droplet "docker stop dashboard_nextjs_prod 2>/dev/null || true"

# Step 3: Create fresh directory structure
echo ""
echo "Step 3: Creating fresh directory on server..."
ssh droplet "rm -rf /srv/ai_receptionist/dashboard_nextjs_new && mkdir -p /srv/ai_receptionist/dashboard_nextjs_new"

# Step 4: Rsync files to new directory
echo ""
echo "Step 4: Syncing files to server..."
rsync -avz --progress \
  --exclude 'node_modules' \
  --exclude '.git' \
  --exclude 'portfolio' \
  --exclude 'lexmakesit-infra' \
  --exclude '.env.local' \
  /home/lex/lexmakesit/frontend/ \
  droplet:/srv/ai_receptionist/dashboard_nextjs_new/

# Step 5: Swap directories
echo ""
echo "Step 5: Swapping directories (atomic)..."
ssh droplet "mv /srv/ai_receptionist/dashboard_nextjs /srv/ai_receptionist/dashboard_nextjs_old 2>/dev/null || true"
ssh droplet "mv /srv/ai_receptionist/dashboard_nextjs_new /srv/ai_receptionist/dashboard_nextjs"

# Step 6: Install production dependencies
echo ""
echo "Step 6: Installing production dependencies on server..."
ssh droplet "cd /srv/ai_receptionist/dashboard_nextjs && npm ci --production"

# Step 7: Start production server
echo ""
echo "Step 7: Starting production server..."
ssh droplet "cd /srv/ai_receptionist/dashboard_nextjs && nohup npm start > /tmp/dashboard.log 2>&1 &"

# Step 8: Health check
echo ""
echo "Step 8: Waiting for server to start..."
sleep 5

ssh droplet "curl -f http://localhost:3000/ > /dev/null" && \
  echo "✅ Dashboard is running!" || \
  (echo "❌ Health check failed. Checking logs..."; ssh droplet "tail -20 /tmp/dashboard.log"; exit 1)

# Cleanup old directory
echo ""
echo "Step 9: Cleaning up old directory..."
ssh droplet "rm -rf /srv/ai_receptionist/dashboard_nextjs_old"

echo ""
echo "✅ Deployment complete!"
echo "Dashboard running at http://receptionlist.ai:3000"
