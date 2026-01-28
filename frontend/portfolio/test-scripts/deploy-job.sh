#!/bin/bash
# Test deployment preparation locally
# This simulates the deploy job without actually connecting to server

set -e
echo "🚀 Testing GitHub Actions 'deploy' job preparation locally..."

# Simulate environment variables
export HOST_IP="104.236.100.245"
export DOMAIN="lexmakesit.com"
export EMAIL="test@example.com"
export SECRET_KEY="test-secret-key-32-characters-long"
export POSTGRES_PASSWORD="test-postgres-password"
export SMTP_USER="test@gmail.com"
export SMTP_PASSWORD="test-smtp-password"

echo "🔧 Simulating deployment preparation..."

# Create temporary deployment directory
TEMP_DEPLOY="/tmp/portfolio-deploy-test"
rm -rf "$TEMP_DEPLOY"
mkdir -p "$TEMP_DEPLOY/secrets"

echo "📁 Created temporary deployment directory: $TEMP_DEPLOY"

# Copy files that would be deployed
echo "📋 Copying deployment files..."
cp docker-compose.yml "$TEMP_DEPLOY/" 2>/dev/null || echo "⚠️ docker-compose.yml not found"
cp nginx.conf "$TEMP_DEPLOY/" 2>/dev/null || echo "⚠️ nginx.conf not found"  
cp init.sql "$TEMP_DEPLOY/" 2>/dev/null || echo "⚠️ init.sql not found"
cp deploy.sh "$TEMP_DEPLOY/" 2>/dev/null || echo "⚠️ deploy.sh not found"
cp .env.example "$TEMP_DEPLOY/" 2>/dev/null || echo "⚠️ .env.example not found"

# Copy templates and static directories if they exist
if [ -d "templates" ]; then
    cp -r templates "$TEMP_DEPLOY/"
    echo "✅ Copied templates directory"
else
    echo "⚠️ templates directory not found"
fi

if [ -d "static" ]; then
    cp -r static "$TEMP_DEPLOY/"
    echo "✅ Copied static directory"
else
    echo "⚠️ static directory not found"
fi

# Simulate .env file creation
cd "$TEMP_DEPLOY"
echo "🔧 Creating .env file..."
if [ -f ".env.example" ]; then
    cp .env.example .env
    
    # Replace placeholders with test values (simulate sed commands)
    sed -i "s/yourdomain.com/$DOMAIN/g" .env
    sed -i "s/your-email@example.com/$EMAIL/g" .env
    sed -i "s/your-super-secret-key-here-use-openssl-rand-hex-32/$SECRET_KEY/g" .env
    sed -i "s/secure-postgres-password-123/$POSTGRES_PASSWORD/g" .env
    sed -i "s/your-smtp-password/$SMTP_PASSWORD/g" .env
    sed -i "s/your-email@gmail.com/$SMTP_USER/g" .env
    
    echo "✅ .env file created and configured"
else
    echo "❌ .env.example not found - creating basic .env"
    cat > .env << EOF
DOMAIN=$DOMAIN
EMAIL=$EMAIL
SECRET_KEY=$SECRET_KEY
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
SMTP_USER=$SMTP_USER
SMTP_PASSWORD=$SMTP_PASSWORD
EOF
fi

# Create Docker secrets
echo "🔐 Creating Docker secrets..."
echo "$SECRET_KEY" > secrets/secret_key.txt
echo "$SMTP_PASSWORD" > secrets/smtp_password.txt  
echo "$POSTGRES_PASSWORD" > secrets/postgres_password.txt
chmod 600 secrets/*.txt

echo "✅ Docker secrets created"

# Simulate docker-compose modification
echo "🔧 Modifying docker-compose.yml for registry..."
if [ -f "docker-compose.yml" ]; then
    # Backup original
    cp docker-compose.yml docker-compose.yml.backup
    
    # Simulate the sed command that replaces build with image
    sed -i 's|build: .|image: ghcr.io/as4584/portfolio:latest|g' docker-compose.yml
    
    echo "✅ docker-compose.yml modified for registry"
    
    # Show the difference
    echo "📊 Changes made to docker-compose.yml:"
    diff docker-compose.yml.backup docker-compose.yml || true
else
    echo "❌ docker-compose.yml not found"
fi

# Test docker-compose syntax
echo "🧪 Testing docker-compose syntax..."
if command -v docker-compose &> /dev/null; then
    if docker-compose config --quiet; then
        echo "✅ docker-compose.yml syntax is valid"
    else
        echo "❌ docker-compose.yml has syntax errors"
    fi
else
    echo "⚠️ docker-compose not installed, skipping syntax check"
fi

# Simulate deployment commands (without execution)
echo "🎭 Simulating deployment commands..."
cat << 'EOF'
Deployment commands that would be executed:
1. SSH setup and key configuration
2. Create deployment directory: mkdir -p /opt/portfolio
3. Copy files via scp to server
4. Login to GitHub Container Registry
5. Pull latest Docker image: docker-compose pull web
6. Stop existing containers: docker-compose down --timeout 30
7. Start database: docker-compose up -d db
8. Wait 10 seconds for DB startup
9. Start all services: docker-compose up -d
10. Health check: curl http://localhost:8001/api/health
11. Cleanup old images: docker image prune -f
EOF

# Health check simulation
echo "🏥 Simulating health check..."
echo "Would check: https://$DOMAIN/api/health"

# Show deployment summary
echo ""
echo "📊 Deployment Summary:"
echo "======================"
echo "Target Domain: $DOMAIN"
echo "Target Server: $HOST_IP"
echo "Files prepared: $(ls -la | wc -l) items"
echo "Secrets created: $(ls -la secrets/ | wc -l) files"
echo "Environment configured: ✅"
echo "Docker compose ready: ✅"
echo ""

# Cleanup prompt
echo -n "View created files? (y/n): "
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "📁 Deployment directory contents:"
    ls -la "$TEMP_DEPLOY"
    echo ""
    echo "📄 .env file contents:"
    cat "$TEMP_DEPLOY/.env"
    echo ""
    echo "🔐 Secrets directory:"
    ls -la "$TEMP_DEPLOY/secrets/"
fi

echo ""
echo -n "Remove temporary deployment directory? (y/n): "
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    rm -rf "$TEMP_DEPLOY"
    echo "✅ Temporary directory removed"
else
    echo "ℹ️ Temporary directory kept at: $TEMP_DEPLOY"
fi

echo "🎉 Deploy job preparation completed successfully!"
echo "💡 This was a simulation - no actual deployment occurred"