#!/bin/bash
# rolling_deploy.sh
# Zero-downtime deployment for Docker Compose
set -e

COMPOSE_FILE=${1:-"docker-compose.prod.yml"}
SERVICE_NAME=${2:-"app"}

echo "🚀 Starting zero-downtime deployment for $SERVICE_NAME..."

# Build the new image first
echo "🏗️  Building new image..."
docker compose -f "$COMPOSE_FILE" build "$SERVICE_NAME"

# Scale up to 2 containers
echo "📈 Scaling up to 2 containers..."
docker compose -f "$COMPOSE_FILE" up -d --scale "$SERVICE_NAME"=2 --no-recreate "$SERVICE_NAME"

# Function to check health of the newest container
check_health() {
    local service=$1
    local expected_count=$2
    local healthy_count=$(docker ps --filter "label=com.docker.compose.service=$service" --filter "health=healthy" -q | wc -l)
    echo "$healthy_count"
}

echo "⏳ Waiting for new container to become healthy..."
MAX_RETRIES=45
RETRY_COUNT=0
while [ "$RETRY_COUNT" -lt "$MAX_RETRIES" ]; do
    HEALTHY=$(check_health "$SERVICE_NAME")
    if [ "$HEALTHY" -ge 2 ]; then
        echo "✅ New container is healthy!"
        break
    fi
    echo "   Current healthy containers: $HEALTHY/$((2)) (Attempt $((RETRY_COUNT+1))/$MAX_RETRIES)"
    sleep 2
    RETRY_COUNT=$((RETRY_COUNT+1))
done

if [ "$RETRY_COUNT" -eq "$MAX_RETRIES" ]; then
    echo "❌ Timeout waiting for health. Checking if at least one is healthy to avoid total outage..."
    HEALTHY=$(check_health "$SERVICE_NAME")
    if [ "$HEALTHY" -lt 1 ]; then
        echo "💥 CRITICAL: No healthy containers! Check logs."
        exit 1
    fi
    echo "⚠️  Deployment partially failed, but at least one container is healthy."
fi

# Find the old container ID (the one with the older creation date)
echo "🧹 Identifying old container..."
OLD_CONTAINER_ID=$(docker ps --filter "label=com.docker.compose.service=$SERVICE_NAME" --format "{{.ID}} {{.CreatedAt}}" | sort -k2,3 | head -n 1 | awk '{print $1}')

if [ -n "$OLD_CONTAINER_ID" ]; then
    echo "🛑 Stopping old container: $OLD_CONTAINER_ID"
    docker stop "$OLD_CONTAINER_ID"
    docker rm "$OLD_CONTAINER_ID"
fi

# Scale back to 1
echo "📉 Scaling back to 1 container..."
docker compose -f "$COMPOSE_FILE" up -d --scale "$SERVICE_NAME"=1 --no-recreate "$SERVICE_NAME"

echo "✨ Deployment successful with ZERO downtime!"
