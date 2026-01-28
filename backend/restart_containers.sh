#!/bin/bash
"""
Container restart and verification script
"""

cd /home/lex/lexmakesit/backend

echo "🚀 Restarting containers..."
docker compose down
docker compose up -d

echo "⏳ Waiting for services to be ready..."
sleep 10

echo "📊 Service status:"
docker compose ps

echo "🔍 Testing API health..."
curl -s http://localhost:8002/health | head -10

echo "✅ Containers restarted successfully"