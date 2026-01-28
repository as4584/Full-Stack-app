#!/bin/bash

# =============================================================================
# Portfolio Production Deployment Script with Let's Encrypt SSL
# =============================================================================
# This script automates the deployment of your portfolio with SSL certificates
# Run with: ./deploy.sh yourdomain.com your-email@example.com
# =============================================================================

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script parameters
DOMAIN=${1:-""}
EMAIL=${2:-""}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Helper functions
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Validate inputs
validate_inputs() {
    if [[ -z "$DOMAIN" ]] || [[ -z "$EMAIL" ]]; then
        print_error "Usage: $0 <domain> <email>"
        print_error "Example: $0 example.com admin@example.com"
        exit 1
    fi

    if ! [[ "$EMAIL" =~ ^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$ ]]; then
        print_error "Invalid email format: $EMAIL"
        exit 1
    fi

    print_info "Domain: $DOMAIN"
    print_info "Email: $EMAIL"
}

# Check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."

    # Check if running as root or with sudo
    if [[ $EUID -ne 0 ]] && ! sudo -n true 2>/dev/null; then
        print_error "This script needs sudo privileges for Docker operations"
        exit 1
    fi

    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi

    # Check if .env file exists
    if [[ ! -f "$SCRIPT_DIR/.env" ]]; then
        print_warning ".env file not found. Creating from template..."
        create_env_file
    fi

    print_success "Prerequisites check passed"
}

# Create .env file from template
create_env_file() {
    if [[ ! -f "$SCRIPT_DIR/.env.example" ]]; then
        print_error ".env.example template not found!"
        exit 1
    fi

    cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
    
    # Replace placeholders with actual values
    sed -i "s/yourdomain.com/$DOMAIN/g" "$SCRIPT_DIR/.env"
    sed -i "s/your-email@example.com/$EMAIL/g" "$SCRIPT_DIR/.env"
    sed -i "s/your-super-secret-key-here-use-openssl-rand-hex-32/$(openssl rand -hex 32)/g" "$SCRIPT_DIR/.env"
    
    # Generate secure passwords
    POSTGRES_PASSWORD=$(openssl rand -base64 32)
    sed -i "s/secure-postgres-password-123/$POSTGRES_PASSWORD/g" "$SCRIPT_DIR/.env"
    
    # Create secrets directory and files
    mkdir -p "$SCRIPT_DIR/secrets"
    echo "$(openssl rand -hex 32)" > "$SCRIPT_DIR/secrets/secret_key.txt"
    echo "your-smtp-password-here" > "$SCRIPT_DIR/secrets/smtp_password.txt"
    echo "$POSTGRES_PASSWORD" > "$SCRIPT_DIR/secrets/postgres_password.txt"
    
    # Set proper permissions on secrets
    chmod 600 "$SCRIPT_DIR/secrets/"*.txt
    
    print_success "Created .env file and Docker secrets with secure passwords"
    print_warning "Please update secrets/smtp_password.txt with your actual SMTP password"
    print_warning "Please review and update .env file with your SMTP and other settings"
    
    # Pause for user to review
    read -p "Press Enter to continue after updating secrets and .env file, or Ctrl+C to abort..."
}

# Create nginx config with domain substitution
prepare_nginx_config() {
    print_info "Preparing nginx configuration for domain: $DOMAIN"
    
    # Replace domain placeholder in nginx.conf
    envsubst '${DOMAIN}' < "$SCRIPT_DIR/nginx.conf" > "$SCRIPT_DIR/nginx.prod.conf"
    
    print_success "Nginx configuration prepared"
}

# Initial certificate generation (dry run first)
generate_ssl_certificate() {
    print_info "Generating SSL certificate for $DOMAIN..."
    
    # First, start nginx without SSL for the initial challenge
    print_info "Starting services for certificate generation..."
    
    # Temporarily modify docker-compose for initial setup
    docker-compose -f docker-compose.yml up -d nginx web
    
    # Wait for nginx to be ready
    sleep 10
    
    # Run certbot to get the certificate
    print_info "Running certbot for certificate generation..."
    docker-compose run --rm certbot certonly \
        --webroot \
        --webroot-path=/var/www/html \
        --email $EMAIL \
        --agree-tos \
        --no-eff-email \
        --staging \
        -d $DOMAIN \
        -d www.$DOMAIN
    
    if [[ $? -eq 0 ]]; then
        print_success "Staging certificate generated successfully"
        print_info "Now generating production certificate..."
        
        # Generate production certificate
        docker-compose run --rm certbot certonly \
            --webroot \
            --webroot-path=/var/www/html \
            --email $EMAIL \
            --agree-tos \
            --no-eff-email \
            --force-renewal \
            -d $DOMAIN \
            -d www.$DOMAIN
        
        if [[ $? -eq 0 ]]; then
            print_success "Production SSL certificate generated successfully"
        else
            print_error "Failed to generate production certificate"
            exit 1
        fi
    else
        print_error "Failed to generate staging certificate"
        exit 1
    fi
}

# Set up SSL certificate renewal
setup_ssl_renewal() {
    print_info "Setting up SSL certificate auto-renewal..."
    
    # Create renewal script
    cat > "$SCRIPT_DIR/renew-ssl.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
docker-compose run --rm certbot renew
docker-compose exec nginx nginx -s reload
EOF

    chmod +x "$SCRIPT_DIR/renew-ssl.sh"
    
    print_info "SSL renewal script created. Add this to crontab:"
    print_warning "0 0 * * 0 $SCRIPT_DIR/renew-ssl.sh"
    
    print_success "SSL renewal setup complete"
}

# Deploy the application
deploy_application() {
    print_info "Deploying application with SSL..."
    
    # Update nginx config to use production SSL config
    cp "$SCRIPT_DIR/nginx.prod.conf" "$SCRIPT_DIR/nginx.conf"
    
    # Restart services with SSL configuration
    docker-compose down
    docker-compose up -d
    
    # Wait for services to be ready
    sleep 15
    
    # Test the deployment
    if curl -f -k "https://$DOMAIN/api/health" &> /dev/null; then
        print_success "Application deployed successfully!"
        print_info "Your portfolio is now available at: https://$DOMAIN"
    else
        print_warning "Application deployed, but health check failed. Check logs:"
        print_info "docker-compose logs"
    fi
}

# Cleanup function
cleanup() {
    print_info "Cleaning up temporary files..."
    [[ -f "$SCRIPT_DIR/nginx.prod.conf" ]] && rm "$SCRIPT_DIR/nginx.prod.conf"
}

# Main execution flow
main() {
    print_info "Starting Portfolio Deployment with Let's Encrypt SSL"
    print_info "=================================================="
    
    validate_inputs
    check_prerequisites
    prepare_nginx_config
    generate_ssl_certificate
    setup_ssl_renewal
    deploy_application
    cleanup
    
    print_success "Deployment complete!"
    print_info "Next steps:"
    print_info "1. Update your DNS to point $DOMAIN to this server"
    print_info "2. Review and update .env file with your SMTP settings"
    print_info "3. Set up SSL renewal cron job (see output above)"
    print_info "4. Monitor logs: docker-compose logs -f"
}

# Set trap for cleanup on exit
trap cleanup EXIT

# Run main function
main "$@"