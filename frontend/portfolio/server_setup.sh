#!/bin/bash

#####################################################################
# DigitalOcean Ubuntu Server Setup Script for Portfolio Website
# Domain: lexmakesit.com
# Backend: FastAPI on http://127.0.0.1:8000
# Features: Nginx reverse proxy + Let's Encrypt SSL
#####################################################################

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOMAIN="lexmakesit.com"
WWW_DOMAIN="www.lexmakesit.com"
BACKEND_URL="http://127.0.0.1:8000"
NGINX_CONFIG_PATH="/etc/nginx/sites-available/portfolio"
NGINX_ENABLED_PATH="/etc/nginx/sites-enabled/portfolio"

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   error "This script must be run as root (use sudo)"
   exit 1
fi

log "🚀 Starting DigitalOcean Ubuntu Server Setup for Portfolio Website"
log "Domain: $DOMAIN and $WWW_DOMAIN"
log "Backend: $BACKEND_URL"

# Update system packages
log "📦 Updating system packages..."
apt update -y
apt upgrade -y

# Install nginx if not already installed
log "🔧 Installing nginx..."
if ! command -v nginx &> /dev/null; then
    apt install nginx -y
    log "✅ Nginx installed successfully"
else
    info "Nginx is already installed"
fi

# Start and enable nginx
log "🔄 Starting and enabling nginx..."
systemctl start nginx
systemctl enable nginx

# Remove default nginx site if it exists
if [[ -f "/etc/nginx/sites-enabled/default" ]]; then
    log "🗑️  Removing default nginx site..."
    rm -f /etc/nginx/sites-enabled/default
fi

# Create nginx configuration for portfolio
log "📝 Creating nginx configuration for portfolio..."
cat > "$NGINX_CONFIG_PATH" << 'EOF'
server {
    listen 80;
    listen [::]:80;
    
    server_name lexmakesit.com www.lexmakesit.com;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    # Client upload size
    client_max_body_size 10M;
    
    location / {
        # Proxy to FastAPI backend
        proxy_pass http://127.0.0.1:8000;
        
        # Required proxy headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
        
        # Handle WebSocket connections if needed
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        access_log off;
    }
    
    # Static files optimization
    location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Security - deny access to sensitive files
    location ~ /\. {
        deny all;
    }
    
    location ~ /(logs/|\.git/) {
        deny all;
    }
}
EOF

log "✅ Nginx configuration created at $NGINX_CONFIG_PATH"

# Enable the site by creating symlink
log "🔗 Enabling portfolio site..."
if [[ -L "$NGINX_ENABLED_PATH" ]]; then
    warn "Portfolio site is already enabled"
else
    ln -s "$NGINX_CONFIG_PATH" "$NGINX_ENABLED_PATH"
    log "✅ Portfolio site enabled"
fi

# Test nginx configuration
log "🧪 Testing nginx configuration..."
if nginx -t; then
    log "✅ Nginx configuration syntax is valid"
else
    error "❌ Nginx configuration syntax error!"
    exit 1
fi

# Restart nginx to apply changes
log "🔄 Restarting nginx..."
systemctl restart nginx

# Check nginx status
if systemctl is-active --quiet nginx; then
    log "✅ Nginx is running successfully"
else
    error "❌ Nginx failed to start!"
    exit 1
fi

# Install snapd and certbot
log "📦 Installing Certbot for SSL certificates..."
if ! command -v snap &> /dev/null; then
    apt install snapd -y
    log "✅ Snapd installed"
else
    info "Snapd is already installed"
fi

# Install certbot via snap
if ! command -v certbot &> /dev/null; then
    snap install core; snap refresh core
    snap install --classic certbot
    
    # Create symlink for certbot command
    if [[ ! -L "/usr/bin/certbot" ]]; then
        ln -s /snap/bin/certbot /usr/bin/certbot
    fi
    log "✅ Certbot installed successfully"
else
    info "Certbot is already installed"
fi

# Install certbot nginx plugin
snap set certbot trust-plugin-with-root=ok
if ! snap list | grep -q certbot-dns-nginx; then
    snap install certbot-dns-nginx
    log "✅ Certbot nginx plugin installed"
else
    info "Certbot nginx plugin is already installed"
fi

# Request SSL certificates
log "🔒 Requesting SSL certificates for $DOMAIN and $WWW_DOMAIN..."

# Check if certificates already exist
if [[ -d "/etc/letsencrypt/live/$DOMAIN" ]]; then
    warn "SSL certificates already exist for $DOMAIN"
    info "Running certificate renewal check..."
    certbot renew --dry-run
else
    # Request new certificates
    info "Requesting new SSL certificates..."
    certbot --nginx -d "$DOMAIN" -d "$WWW_DOMAIN" --non-interactive --agree-tos --email admin@"$DOMAIN" --redirect
    
    if [[ $? -eq 0 ]]; then
        log "✅ SSL certificates obtained and configured successfully"
    else
        error "❌ Failed to obtain SSL certificates"
        warn "You may need to:"
        warn "1. Ensure your domain DNS points to this server's IP"
        warn "2. Check if port 80 and 443 are accessible"
        warn "3. Run the certificate command manually:"
        warn "   certbot --nginx -d $DOMAIN -d $WWW_DOMAIN"
    fi
fi

# Setup automatic certificate renewal
log "⚙️  Setting up automatic certificate renewal..."
if ! crontab -l 2>/dev/null | grep -q certbot; then
    (crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -
    log "✅ Automatic certificate renewal configured"
else
    info "Automatic certificate renewal is already configured"
fi

# Final nginx restart to ensure all changes are applied
log "🔄 Final nginx restart..."
systemctl restart nginx

# Display status
log "📋 Setup Summary:"
echo "=================================="
echo "🌐 Domain: $DOMAIN, $WWW_DOMAIN"
echo "🔧 Nginx: $(nginx -v 2>&1)"
echo "🔒 SSL: $(if [[ -d "/etc/letsencrypt/live/$DOMAIN" ]]; then echo "✅ Configured"; else echo "❌ Not configured"; fi)"
echo "🚀 Backend: $BACKEND_URL"
echo "📁 Nginx config: $NGINX_CONFIG_PATH"
echo "🔗 Site enabled: $NGINX_ENABLED_PATH"
echo "=================================="

# Test the setup
log "🧪 Testing the setup..."
echo "Testing nginx status..."
systemctl status nginx --no-pager -l

echo ""
echo "Testing domain resolution (if DNS is configured)..."
if command -v curl &> /dev/null; then
    curl -I "http://localhost" 2>/dev/null | head -1 || warn "Backend may not be running on port 8000"
else
    warn "curl not available for testing"
fi

log "🎉 Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Ensure your FastAPI application is running on port 8000"
echo "2. Point your domain DNS to this server's IP address"
echo "3. If SSL setup failed, run: certbot --nginx -d $DOMAIN -d $WWW_DOMAIN"
echo "4. Test your website: https://$DOMAIN"
echo ""
echo "Useful commands:"
echo "- Check nginx status: systemctl status nginx"
echo "- View nginx logs: tail -f /var/log/nginx/access.log"
echo "- Test nginx config: nginx -t"
echo "- Restart nginx: systemctl restart nginx"
echo "- Check SSL certificates: certbot certificates"
echo ""

log "✅ DigitalOcean Ubuntu Server Setup Complete!"