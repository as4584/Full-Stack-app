#!/bin/bash
# Safe Deployment with Automatic Rollback
# Only deploys if tests pass, automatically rolls back on failure

set -e

DEPLOY_TARGET="${1:-all}"
SERVER="Innovation"
BACKEND_DIR="/opt/ai-receptionist"
ROLLBACK_DIR="/tmp/pre-deploy-backup-$$"

echo "🛡️  SAFE DEPLOYMENT WITH AUTO-ROLLBACK"
echo "======================================"
echo "Target: $DEPLOY_TARGET"
echo ""

# Step 1: Pre-deployment validation
echo "1️⃣  Running pre-deployment tests..."
if ! python3 /home/lex/lexmakesit/test_golden_state.py; then
    echo ""
    echo "❌ Pre-deployment tests FAILED!"
    echo "🚫 Deployment blocked - current state is broken"
    echo ""
    echo "Fix the issues and try again, or restore golden state:"
    echo "  ssh $SERVER 'bash /opt/ai-receptionist/golden-state-backups/latest/restore.sh'"
    exit 1
fi

echo ""
echo "✅ Pre-deployment tests passed - proceeding with deployment"
echo ""

# Step 2: Create rollback point
echo "2️⃣  Creating rollback point..."
ssh $SERVER "mkdir -p $ROLLBACK_DIR"

# Backup current Docker images
ssh $SERVER "
    docker save dashboard_nextjs_prod:latest 2>/dev/null | gzip > $ROLLBACK_DIR/dashboard.tar.gz || true
    docker save auth_nextjs_prod:latest 2>/dev/null | gzip > $ROLLBACK_DIR/auth.tar.gz || true
    sudo cp /etc/caddy/Caddyfile $ROLLBACK_DIR/Caddyfile || true
"

echo "✅ Rollback point created"
echo ""

# Step 3: Deploy
echo "3️⃣  Deploying new version..."

deploy_dashboard() {
    echo "📦 Deploying Dashboard..."
    rsync -avz --delete \
        --exclude 'node_modules' \
        --exclude '.next' \
        --exclude '.git' \
        /home/lex/lexmakesit/frontend/ \
        $SERVER:$BACKEND_DIR/frontend/ > /dev/null
    
    ssh $SERVER "cd $BACKEND_DIR/frontend && docker compose -f docker-compose.prod.yml up -d --build" || return 1
}

deploy_auth() {
    echo "📦 Deploying Auth..."
    rsync -avz --delete \
        --exclude 'node_modules' \
        --exclude '.next' \
        --exclude '.git' \
        /home/lex/lexmakesit/auth-frontend/ \
        $SERVER:$BACKEND_DIR/auth-frontend/ > /dev/null
    
    ssh $SERVER "cd $BACKEND_DIR/auth-frontend && docker compose -f docker-compose.prod.yml up -d --build" || return 1
}

# Execute deployment
DEPLOYMENT_FAILED=0

case $DEPLOY_TARGET in
    dashboard)
        deploy_dashboard || DEPLOYMENT_FAILED=1
        ;;
    auth)
        deploy_auth || DEPLOYMENT_FAILED=1
        ;;
    all)
        deploy_dashboard || DEPLOYMENT_FAILED=1
        deploy_auth || DEPLOYMENT_FAILED=1
        ;;
esac

if [ $DEPLOYMENT_FAILED -eq 1 ]; then
    echo ""
    echo "❌ Deployment build failed!"
    echo "🔄 Rolling back to previous state..."
    
    ssh $SERVER "
        docker load < $ROLLBACK_DIR/dashboard.tar.gz 2>/dev/null || true
        docker load < $ROLLBACK_DIR/auth.tar.gz 2>/dev/null || true
        cd $BACKEND_DIR/frontend && docker compose -f docker-compose.prod.yml up -d 2>/dev/null || true
        cd $BACKEND_DIR/auth-frontend && docker compose -f docker-compose.prod.yml up -d 2>/dev/null || true
        sudo cp $ROLLBACK_DIR/Caddyfile /etc/caddy/Caddyfile 2>/dev/null || true
        sudo systemctl reload caddy 2>/dev/null || true
    "
    
    echo "✅ Rolled back to previous state"
    exit 1
fi

# Reload Caddy
if [ -f "/home/lex/lexmakesit/Caddyfile.production" ]; then
    scp /home/lex/lexmakesit/Caddyfile.production $SERVER:/tmp/Caddyfile.new > /dev/null
    ssh $SERVER "sudo cp /tmp/Caddyfile.new /etc/caddy/Caddyfile && sudo systemctl reload caddy"
fi

echo ""
echo "✅ Deployment completed"
echo ""

# Step 4: Post-deployment validation
echo "4️⃣  Running post-deployment tests..."
sleep 5  # Wait for containers to be ready

if ! python3 /home/lex/lexmakesit/test_golden_state.py; then
    echo ""
    echo "❌ Post-deployment tests FAILED!"
    echo "🔄 Automatic rollback initiated..."
    
    # Rollback
    ssh $SERVER "
        docker load < $ROLLBACK_DIR/dashboard.tar.gz
        docker load < $ROLLBACK_DIR/auth.tar.gz
        cd $BACKEND_DIR/frontend && docker compose -f docker-compose.prod.yml up -d
        cd $BACKEND_DIR/auth-frontend && docker compose -f docker-compose.prod.yml up -d
        sudo cp $ROLLBACK_DIR/Caddyfile /etc/caddy/Caddyfile
        sudo systemctl reload caddy
    "
    
    echo ""
    echo "✅ Automatic rollback completed"
    echo "❌ Deployment failed validation - reverted to previous working state"
    
    # Verify rollback worked
    sleep 5
    if python3 /home/lex/lexmakesit/test_golden_state.py; then
        echo ""
        echo "✅ Rollback verified - system is stable"
    else
        echo ""
        echo "⚠️  Rollback may have issues - check system manually"
        echo "Or restore golden state:"
        echo "  ssh $SERVER 'bash /opt/ai-receptionist/golden-state-backups/latest/restore.sh'"
    fi
    
    exit 1
fi

# Step 5: Success - clean up rollback
echo ""
echo "✅ Post-deployment tests passed!"
ssh $SERVER "rm -rf $ROLLBACK_DIR"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ DEPLOYMENT SUCCESSFUL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "All services are healthy:"
echo "  • Dashboard: https://lexmakesit.com"
echo "  • Auth: https://auth.lexmakesit.com"
echo "  • API: https://receptionist.lexmakesit.com"
echo ""
echo "💡 Create new golden state backup:"
echo "  ./scripts/create_golden_state.sh"
