#!/bin/bash
set -e

echo "=== POST-DEPLOY VERIFICATION GATE ==="
echo ""

# Run smoke test
if /home/lex/lexmakesit/scripts/smoke-test-production.sh; then
    echo ""
    echo "✓ Smoke test passed. Deploy successful."
    
    # Log successful deployment
    ssh droplet "echo '[$(date)] Deploy successful - dashboard.lexmakesit.com' >> /var/log/deployments.log"
    
    exit 0
else
    echo ""
    echo "✗ Smoke test FAILED. Initiating rollback..."
    
    # Rollback: restart previous container or mark deploy as failed
    ssh droplet "cd /srv/ai_receptionist/dashboard_src && docker compose -f docker-compose.prod.locked.yml down"
    
    # Log failed deployment
    ssh droplet "echo '[$(date)] Deploy FAILED - smoke test failed' >> /var/log/deployments.log"
    
    echo ""
    echo "Deploy marked as FAILED. Manual intervention required."
    exit 1
fi
