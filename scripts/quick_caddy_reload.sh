#!/bin/bash
# Quick Caddy reload script
# Copies Caddyfile and reloads Caddy in one command

set -e

SERVER="Innovation"
CADDYFILE="/home/lex/lexmakesit/Caddyfile.production"

if [ ! -f "$CADDYFILE" ]; then
    echo "❌ Caddyfile not found: $CADDYFILE"
    exit 1
fi

echo "🔄 Reloading Caddy configuration..."

# Copy Caddyfile to server
scp $CADDYFILE $SERVER:/tmp/Caddyfile.new

# Move to proper location and reload
ssh $SERVER "sudo cp /tmp/Caddyfile.new /etc/caddy/Caddyfile && sudo systemctl reload caddy"

# Wait and verify
sleep 2

echo ""
echo "✅ Caddy reloaded successfully!"
echo ""
echo "Testing endpoints..."
curl -I https://lexmakesit.com/ 2>&1 | head -2
curl -I https://auth.lexmakesit.com/ 2>&1 | head -2
