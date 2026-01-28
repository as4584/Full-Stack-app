#!/bin/bash
# Test the "build" job from GitHub Actions locally
# This script replicates Docker build and push steps

set -e
echo "🏗️ Testing GitHub Actions 'build' job locally..."

# Check Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed or not running"
    exit 1
fi

echo "🐳 Docker version:"
docker version --format 'Client: {{.Client.Version}}, Server: {{.Server.Version}}'

# Simulate metadata extraction
echo "📋 Extracting metadata..."
REGISTRY="ghcr.io"
IMAGE_NAME="as4584/portfolio"
BRANCH=$(git branch --show-current)
COMMIT_SHA=$(git rev-parse --short HEAD)

echo "Registry: $REGISTRY"
echo "Image name: $IMAGE_NAME"
echo "Branch: $BRANCH"
echo "Commit: $COMMIT_SHA"

# Generate tags like in the workflow
TAGS=(
    "$REGISTRY/$IMAGE_NAME:$BRANCH"
    "$REGISTRY/$IMAGE_NAME:$BRANCH-$COMMIT_SHA"
)

if [ "$BRANCH" = "main" ]; then
    TAGS+=("$REGISTRY/$IMAGE_NAME:latest")
fi

echo "Generated tags:"
for tag in "${TAGS[@]}"; do
    echo "  - $tag"
done

# Build Docker image (without pushing)
echo "🏗️ Building Docker image..."
LOCAL_TAG="portfolio-local-test:latest"

if docker build -t "$LOCAL_TAG" .; then
    echo "✅ Docker build successful!"
    
    # Test the built image
    echo "🧪 Testing built image..."
    
    # Start container in background
    CONTAINER_ID=$(docker run -d -p 8003:8001 \
        -e DATABASE_URL="sqlite:///./test.db" \
        -e PRODUCTION="false" \
        -e SECRET_KEY="test-local-build" \
        "$LOCAL_TAG")
    
    echo "Started container: $CONTAINER_ID"
    
    # Wait for startup
    echo "⏳ Waiting for container to start..."
    sleep 10
    
    # Test health endpoint
    if curl -f http://localhost:8003/api/health &>/dev/null; then
        echo "✅ Container health check passed!"
    else
        echo "⚠️ Container health check failed"
        echo "Container logs:"
        docker logs "$CONTAINER_ID" --tail 20
    fi
    
    # Cleanup
    echo "🧹 Cleaning up..."
    docker stop "$CONTAINER_ID" 2>/dev/null || true
    docker rm "$CONTAINER_ID" 2>/dev/null || true
    
    echo "🎯 Build job simulation completed!"
    
    # Show image details
    echo "📊 Built image details:"
    docker images "$LOCAL_TAG" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
    
    # Option to cleanup
    echo ""
    echo -n "Remove test image? (y/n): "
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        docker rmi "$LOCAL_TAG" --force
        echo "✅ Test image removed"
    else
        echo "ℹ️ Test image kept: $LOCAL_TAG"
    fi
    
else
    echo "❌ Docker build failed!"
    exit 1
fi

echo "🎉 Build job completed successfully!"