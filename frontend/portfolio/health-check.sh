#!/bin/bash

# =============================================================================
# Deployment Health Check Script
# =============================================================================
# This script verifies that the deployment is successful and all services are healthy
# Used by CI/CD pipeline and can be run manually for troubleshooting
# =============================================================================

set -e

DOMAIN=${1:-"lexmakesit.com"}
MAX_RETRIES=12
RETRY_DELAY=10

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

check_service() {
    local url=$1
    local service_name=$2
    local retries=0
    
    print_info "Checking $service_name at $url..."
    
    while [ $retries -lt $MAX_RETRIES ]; do
        if curl -f -s -m 10 "$url" > /dev/null; then
            print_success "$service_name is responding"
            return 0
        fi
        
        retries=$((retries + 1))
        print_warning "Attempt $retries/$MAX_RETRIES failed for $service_name, retrying in ${RETRY_DELAY}s..."
        sleep $RETRY_DELAY
    done
    
    print_error "$service_name failed health check after $MAX_RETRIES attempts"
    return 1
}

check_ssl_certificate() {
    print_info "Checking SSL certificate for $DOMAIN..."
    
    if openssl s_client -connect "$DOMAIN:443" -servername "$DOMAIN" < /dev/null 2>/dev/null | openssl x509 -noout -dates; then
        print_success "SSL certificate is valid"
        return 0
    else
        print_error "SSL certificate check failed"
        return 1
    fi
}

check_docker_services() {
    print_info "Checking Docker services status..."
    
    # Check if we can access docker-compose
    if ! command -v docker-compose &> /dev/null; then
        print_warning "docker-compose not available, skipping container checks"
        return 0
    fi
    
    # Check if we're in the right directory
    if [ ! -f "docker-compose.yml" ]; then
        print_warning "docker-compose.yml not found in current directory, skipping container checks"
        return 0
    fi
    
    # Check container health
    local unhealthy_containers=$(docker-compose ps --services --filter "status=running" | xargs -I {} sh -c 'docker-compose ps {} | grep -v "healthy\|Up"' | wc -l)
    
    if [ "$unhealthy_containers" -eq 0 ]; then
        print_success "All Docker containers are healthy"
        return 0
    else
        print_error "Some Docker containers are not healthy"
        docker-compose ps
        return 1
    fi
}

check_database_connection() {
    print_info "Checking database connection..."
    
    # Try to connect to the health endpoint which checks the database
    if curl -f -s "https://$DOMAIN/api/health" | grep -q "healthy"; then
        print_success "Database connection is working"
        return 0
    else
        print_error "Database connection check failed"
        return 1
    fi
}

check_performance() {
    print_info "Running basic performance checks..."
    
    local response_time=$(curl -o /dev/null -s -w '%{time_total}' "https://$DOMAIN/")
    local response_time_ms=$(echo "$response_time * 1000" | bc -l | cut -d. -f1)
    
    if [ "$response_time_ms" -lt 2000 ]; then
        print_success "Response time: ${response_time_ms}ms (good)"
    elif [ "$response_time_ms" -lt 5000 ]; then
        print_warning "Response time: ${response_time_ms}ms (acceptable)"
    else
        print_error "Response time: ${response_time_ms}ms (slow)"
        return 1
    fi
}

main() {
    print_info "Starting health check for $DOMAIN"
    echo ""
    
    local failed_checks=0
    
    # Basic connectivity checks
    check_service "https://$DOMAIN/" "Homepage" || failed_checks=$((failed_checks + 1))
    check_service "https://$DOMAIN/api/health" "Health API" || failed_checks=$((failed_checks + 1))
    
    # SSL certificate check
    check_ssl_certificate || failed_checks=$((failed_checks + 1))
    
    # Docker services check (if available)
    check_docker_services || failed_checks=$((failed_checks + 1))
    
    # Database connection check
    check_database_connection || failed_checks=$((failed_checks + 1))
    
    # Performance check
    if command -v bc &> /dev/null; then
        check_performance || failed_checks=$((failed_checks + 1))
    else
        print_warning "bc not available, skipping performance check"
    fi
    
    echo ""
    if [ $failed_checks -eq 0 ]; then
        print_success "🎉 All health checks passed! Deployment is successful."
        print_info "Your portfolio is live at: https://$DOMAIN"
        exit 0
    else
        print_error "❌ $failed_checks health check(s) failed."
        print_info "Check the logs above for details."
        exit 1
    fi
}

# Show usage if help is requested
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Usage: $0 [domain]"
    echo ""
    echo "Examples:"
    echo "  $0                    # Check lexmakesit.com (default)"
    echo "  $0 example.com        # Check custom domain"
    echo ""
    echo "This script performs comprehensive health checks including:"
    echo "  - Website accessibility"
    echo "  - API endpoint functionality"
    echo "  - SSL certificate validity"
    echo "  - Docker container health"
    echo "  - Database connectivity"
    echo "  - Basic performance metrics"
    exit 0
fi

main