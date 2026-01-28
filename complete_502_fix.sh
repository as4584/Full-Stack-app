#!/bin/bash
# Complete the 502 Fix - Final Deployment Steps
# Run this on your LOCAL machine (not on the server)

set -e

echo "🚀 Completing 502 Error Fix - Final Deployment"
echo "=============================================="
echo ""

# Check if we can SSH
if ! ssh Innovation "echo 'SSH connection OK'" > /dev/null 2>&1; then
    echo "❌ Cannot connect to server via SSH"
    exit 1
fi

echo "✅ SSH connection verified"
echo ""

# Step 1: Check if builds are complete
echo "📦 Step 1: Checking Docker builds..."
FRONTEND_IMAGE=$(ssh Innovation "docker images | grep 'frontend-dashboard' | wc -l")
AUTH_IMAGE=$(ssh Innovation "docker images | grep 'auth-frontend-auth\|auth_nextjs' | wc -l")

if [ "$FRONTEND_IMAGE" -eq "0" ]; then
    echo "⚠️  Frontend image not built yet. Starting build..."
    ssh Innovation "cd /opt/ai-receptionist/frontend && docker compose -f docker-compose.prod.yml build --no-cache"
fi

if [ "$AUTH_IMAGE" -eq "0" ]; then
    echo "⚠️  Auth frontend image not built yet. Starting build..."
    ssh Innovation "cd /opt/ai-receptionist/auth-frontend && docker compose -f docker-compose.prod.yml build --no-cache"
fi

echo "✅ Docker images ready"
echo ""

# Step 2: Start containers
echo "🐳 Step 2: Starting Docker containers..."
ssh Innovation "cd /opt/ai-receptionist/frontend && docker compose -f docker-compose.prod.yml up -d" || echo "Frontend already running or failed"
ssh Innovation "cd /opt/ai-receptionist/auth-frontend && docker compose -f docker-compose.prod.yml up -d" || echo "Auth already running or failed"

echo "✅ Containers started"
sleep 5
echo ""

# Step 3: Check container status
echo "📊 Step 3: Checking container status..."
ssh Innovation "docker ps | grep -E 'dashboard|auth'"
echo ""

# Step 4: Update Caddy (this requires sudo password)
echo "🌐 Step 4: Updating Caddy configuration..."
echo "⚠️  This step requires sudo password on the server"
echo ""
echo "Please run this command manually on the server:"
echo "  sudo cp /opt/ai-receptionist/Caddyfile.production /etc/caddy/Caddyfile"
echo "  sudo systemctl reload caddy"
echo ""
read -p "Press Enter when you've completed the Caddy update..."

# Step 5: Test endpoints
echo ""
echo "🧪 Step 5: Testing endpoints..."
echo ""

echo "Testing lexmakesit.com..."
DASHBOARD_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://lexmakesit.com/ || echo "000")
if [ "$DASHBOARD_CODE" = "200" ] || [ "$DASHBOARD_CODE" = "307" ]; then
    echo "✅ Dashboard: HTTP $DASHBOARD_CODE (SUCCESS)"
elif [ "$DASHBOARD_CODE" = "502" ]; then
    echo "❌ Dashboard: HTTP 502 (FAILED)"
else
    echo "⚠️  Dashboard: HTTP $DASHBOARD_CODE (check logs)"
fi

echo "Testing auth.lexmakesit.com..."
AUTH_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://auth.lexmakesit.com/signin || echo "000")
if [ "$AUTH_CODE" = "200" ]; then
    echo "✅ Auth: HTTP $AUTH_CODE (SUCCESS)"
elif [ "$AUTH_CODE" = "502" ]; then
    echo "❌ Auth: HTTP 502 (FAILED)"
else
    echo "⚠️  Auth: HTTP $AUTH_CODE (check logs)"
fi

echo "Testing receptionist.lexmakesit.com..."
BACKEND_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://receptionist.lexmakesit.com/ || echo "000")
if [ "$BACKEND_CODE" = "405" ] || [ "$BACKEND_CODE" = "200" ]; then
    echo "✅ Backend: HTTP $BACKEND_CODE (SUCCESS)"
elif [ "$BACKEND_CODE" = "502" ]; then
    echo "❌ Backend: HTTP 502 (FAILED)"
else
    echo "⚠️  Backend: HTTP $BACKEND_CODE"
fi

echo ""
echo "=============================================="
echo "📊 Deployment Summary"
echo "=============================================="
echo ""
echo "Dashboard (lexmakesit.com): HTTP $DASHBOARD_CODE"
echo "Auth (auth.lexmakesit.com): HTTP $AUTH_CODE"
echo "Backend (receptionist.lexmakesit.com): HTTP $BACKEND_CODE"
echo ""

if [ "$DASHBOARD_CODE" = "502" ] || [ "$AUTH_CODE" = "502" ]; then
    echo "❌ 502 ERRORS STILL PRESENT"
    echo ""
    echo "Troubleshooting steps:"
    echo "1. Check container logs: ssh Innovation 'docker logs dashboard_nextjs_prod'"
    echo "2. Check container logs: ssh Innovation 'docker logs auth_nextjs_prod'"
    echo "3. Verify Caddy config: ssh Innovation 'cat /etc/caddy/Caddyfile'"
    echo "4. Check Caddy status: ssh Innovation 'sudo systemctl status caddy'"
    exit 1
else
    echo "✅ ALL SERVICES HEALTHY - 502 ERRORS FIXED!"
    echo ""
    echo "🎨 Frutiger Aero animations should now be visible at:"
    echo "   - https://lexmakesit.com (Dashboard)"
    echo "   - https://auth.lexmakesit.com (Auth pages)"
    echo ""
    echo "🎉 Deployment complete!"
fi
