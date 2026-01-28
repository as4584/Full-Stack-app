#!/bin/bash
# Quick fix: Restart Caddy and verify health

set -e

echo "🔄 Restarting Caddy..."

# Try passwordless sudo first, fall back to -t if needed
if ssh Innovation 'sudo -n systemctl restart caddy' 2>/dev/null; then
    echo "✅ Caddy restarted (passwordless)"
else
    echo "⚠️  Need sudo password..."
    ssh -t Innovation 'sudo systemctl restart caddy'
fi

echo "⏳ Waiting for Caddy to stabilize..."
sleep 3

echo ""
echo "🔍 Running precision health test..."
echo ""

cd /home/lex/lexmakesit
python3 test_production_health.py

# Exit with same code as health test
exit $?
