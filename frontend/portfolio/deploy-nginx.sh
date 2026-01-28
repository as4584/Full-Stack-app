#!/bin/bash

# 🚀 Portfolio Deployment with Nginx Reverse Proxy + SSL
# Run this script on your DigitalOcean server

echo "🚀 Setting up Portfolio with Nginx Reverse Proxy + SSL..."

# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install Docker and Docker Compose
if ! command -v docker &> /dev/null; then
    echo "📦 Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
fi

if ! command -v docker-compose &> /dev/null; then
    echo "📦 Installing Docker Compose..."
    sudo apt install docker-compose -y
fi

# 3. Install Certbot for SSL
echo "🔐 Installing Certbot for SSL certificates..."
sudo apt install certbot python3-certbot-nginx -y

# 4. Update DNS first (manual step)
echo "⚠️  IMPORTANT: Before continuing, make sure your DNS is set up:"
echo "   1. Go to your GoDaddy domain settings"
echo "   2. Add A record: @ → 104.236.100.245"
echo "   3. Add A record: www → 104.236.100.245"
echo "   4. Wait 5-15 minutes for DNS propagation"
echo ""
read -p "Press ENTER when DNS is configured and propagated..."

# 5. Start with HTTP only first
echo "🌐 Starting portfolio with HTTP (for SSL setup)..."
cp nginx.simple.conf nginx.conf
# Remove SSL lines for initial setup
sed -i '/ssl_/d' nginx.conf
sed -i 's/443 ssl http2/80/' nginx.conf
sed -i 's/https:/http:/' nginx.conf

# 6. Build and start services
docker-compose -f docker-compose.simple.yml down
docker-compose -f docker-compose.simple.yml up -d

# 7. Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 30

# 8. Test HTTP access
echo "🧪 Testing HTTP access..."
if curl -f http://lexmakesit.com > /dev/null 2>&1; then
    echo "✅ HTTP is working!"
else
    echo "❌ HTTP test failed. Check your DNS and try again."
    exit 1
fi

# 9. Get SSL certificate
echo "🔐 Getting SSL certificate from Let's Encrypt..."
sudo certbot --nginx -d lexmakesit.com -d www.lexmakesit.com --non-interactive --agree-tos --email as42519256@gmail.com

# 10. Restart with full SSL configuration
echo "🔄 Restarting with full SSL configuration..."
cp nginx.simple.conf nginx.conf
docker-compose -f docker-compose.simple.yml restart nginx

# 11. Final test
echo "🧪 Testing HTTPS access..."
sleep 10
if curl -f https://lexmakesit.com > /dev/null 2>&1; then
    echo "✅ SUCCESS! Your portfolio is live at https://lexmakesit.com"
    echo "🌟 Features enabled:"
    echo "   - HTTPS with Let's Encrypt SSL"
    echo "   - Nginx reverse proxy"
    echo "   - Rate limiting (5 req/sec)"
    echo "   - Security headers"
    echo "   - Auto HTTP → HTTPS redirect"
else
    echo "⚠️  HTTPS might still be setting up. Try https://lexmakesit.com in a few minutes."
fi

echo ""
echo "🎉 Deployment complete!"
echo "📍 Your portfolio: https://lexmakesit.com"
echo "🔧 Manage with: docker-compose -f docker-compose.simple.yml [up|down|logs]"