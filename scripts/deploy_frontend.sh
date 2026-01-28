#!/bin/bash
# Automated frontend deployment with Caddy reload
# Usage: ./deploy_frontend.sh [dashboard|auth|all]

set -e

DEPLOY_TARGET="${1:-all}"
SERVER="Innovation"
BACKEND_DIR="/opt/ai-receptionist"

echo "🚀 Automated Frontend Deployment"
echo "================================"
echo "Target: $DEPLOY_TARGET"
echo ""

deploy_dashboard() {
    echo "📦 Deploying Dashboard Frontend..."
    
    # Sync files
    rsync -avz --delete \
        --exclude 'node_modules' \
        --exclude '.next' \
        --exclude '.git' \
        /home/lex/lexmakesit/frontend/ \
        $SERVER:$BACKEND_DIR/frontend/
    
    # Build and restart
    ssh $SERVER "cd $BACKEND_DIR/frontend && docker compose -f docker-compose.prod.yml up -d --build"
    
    echo "✅ Dashboard deployed"
}

deploy_auth() {
    echo "📦 Deploying Auth Frontend..."
    
    # Sync files
    rsync -avz --delete \
        --exclude 'node_modules' \
        --exclude '.next' \
        --exclude '.git' \
        /home/lex/lexmakesit/auth-frontend/ \
        $SERVER:$BACKEND_DIR/auth-frontend/
    
    # Build and restart
    ssh $SERVER "cd $BACKEND_DIR/auth-frontend && docker compose -f docker-compose.prod.yml up -d --build"
    
    echo "✅ Auth deployed"
}

reload_caddy() {
    echo "🔄 Reloading Caddy..."
    
    # Copy Caddy config if it exists
    if [ -f "/home/lex/lexmakesit/Caddyfile.production" ]; then
        scp /home/lex/lexmakesit/Caddyfile.production $SERVER:/tmp/Caddyfile.new
        ssh $SERVER "sudo cp /tmp/Caddyfile.new /etc/caddy/Caddyfile"
    fi
    
    # Reload Caddy (passwordless if sudoers configured)
    ssh $SERVER "sudo systemctl reload caddy"
    
    # Wait for Caddy to be ready
    sleep 2
    
    echo "✅ Caddy reloaded"
}

verify_deployment() {
    echo ""
    echo "🔍 Verifying deployment..."
    
    # Wait for containers to be healthy
    sleep 5
    
    # Check dashboard
    if ssh $SERVER "curl -s -o /dev/null -w '%{http_code}' http://localhost:3000" | grep -q "200\|307"; then
        echo "✅ Dashboard container healthy (localhost:3000)"
    else
        echo "⚠️  Dashboard container not responding"
    fi
    
    # Check auth
    if ssh $SERVER "curl -s -o /dev/null -w '%{http_code}' http://localhost:3001" | grep -q "200\|404"; then
        echo "✅ Auth container healthy (localhost:3001)"
    else
        echo "⚠️  Auth container not responding"
    fi
    
    # Check public URLs
    echo ""
    echo "Testing public URLs..."
    
    if curl -s -o /dev/null -w '%{http_code}' https://lexmakesit.com | grep -q "200\|307"; then
        echo "✅ https://lexmakesit.com is live"
    else
        echo "❌ https://lexmakesit.com not accessible"
    fi
    
    if curl -s -o /dev/null -w '%{http_code}' https://auth.lexmakesit.com/signin | grep -q "200\|404"; then
        echo "✅ https://auth.lexmakesit.com is live"
    else
        echo "❌ https://auth.lexmakesit.com not accessible"
    fi
}

# Main deployment flow
case $DEPLOY_TARGET in
    dashboard)
        deploy_dashboard
        ;;
    auth)
        deploy_auth
        ;;
    all)
        deploy_dashboard
        deploy_auth
        ;;
    *)
        echo "❌ Invalid target: $DEPLOY_TARGET"
        echo "Usage: $0 [dashboard|auth|all]"
        exit 1
        ;;
esac

reload_caddy
verify_deployment

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Run health test: python3 test_production_health.py"
