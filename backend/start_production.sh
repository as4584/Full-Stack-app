#!/bin/bash
"""
AI Receptionist Production Startup Script

This script launches the complete AI Receptionist system with PostgreSQL,
runs data seeding, and verifies everything is working correctly.

Usage:
    ./start_production.sh [--reset-data]

Options:
    --reset-data    Drop existing database and recreate (DESTRUCTIVE)
"""

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

title() {
    echo -e "\n${BOLD}${BLUE}$1${NC}"
    echo "$(echo "$1" | sed 's/./=/g')"
}

# Check prerequisites
check_prerequisites() {
    title "🔍 Checking Prerequisites"
    
    # Check Docker
    if command -v docker >/dev/null 2>&1; then
        success "Docker is available"
    elif command -v docker.exe >/dev/null 2>&1; then
        success "Docker Desktop is available"
        # Create alias for docker command
        alias docker=docker.exe
        alias docker-compose=docker-compose.exe
    else
        error "Docker not found. Please install Docker Desktop and enable WSL integration."
        exit 1
    fi
    
    # Check docker-compose
    if command -v docker-compose >/dev/null 2>&1 || command -v docker-compose.exe >/dev/null 2>&1; then
        success "Docker Compose is available"
    else
        error "Docker Compose not found"
        exit 1
    fi
    
    # Check Python
    if command -v python3 >/dev/null 2>&1; then
        success "Python 3 is available"
    else
        error "Python 3 not found"
        exit 1
    fi
    
    # Check configuration files
    if [[ -f ".env" ]] && [[ -f "docker-compose.prod.yml" ]]; then
        success "Configuration files found"
    else
        error "Missing configuration files (.env or docker-compose.prod.yml)"
        exit 1
    fi
}

# Create required directories
create_directories() {
    title "📁 Creating Required Directories"
    
    mkdir -p backups/database
    mkdir -p logs
    
    success "Directories created"
}

# Setup Docker network
setup_network() {
    title "🌐 Setting Up Docker Network"
    
    if docker network ls | grep -q lex_net; then
        log "Network lex_net already exists"
    else
        docker network create lex_net
        success "Created network: lex_net"
    fi
}

# Start PostgreSQL and supporting services
start_services() {
    title "🚀 Starting Database Services"
    
    log "Starting PostgreSQL, Redis, and Qdrant..."
    
    # Start only the database services first
    docker-compose -f docker-compose.prod.yml up -d postgres redis qdrant
    
    log "Waiting for services to be healthy..."
    
    # Wait for PostgreSQL to be ready
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if docker-compose -f docker-compose.prod.yml exec -T postgres pg_isready -U ai_receptionist_user -d ai_receptionist >/dev/null 2>&1; then
            success "PostgreSQL is ready"
            break
        fi
        
        log "Waiting for PostgreSQL... (attempt $attempt/$max_attempts)"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    if [[ $attempt -gt $max_attempts ]]; then
        error "PostgreSQL failed to start within timeout"
        exit 1
    fi
    
    # Wait a bit more for full initialization
    sleep 3
    success "Database services are running"
}

# Run database migrations
run_migrations() {
    title "🔄 Running Database Migrations"
    
    log "Applying database schema..."
    
    # Check if alembic is available, if not install it
    if ! python3 -c "import alembic" 2>/dev/null; then
        log "Installing required dependencies..."
        pip3 install alembic psycopg2-binary sqlalchemy
    fi
    
    # Run migrations
    if [[ -f "alembic.ini" ]]; then
        python3 -m alembic upgrade head
        success "Database migrations completed"
    else
        warning "No alembic.ini found, skipping migrations"
    fi
}

# Seed business data
seed_business_data() {
    title "🌱 Seeding Business Data"
    
    log "Restoring AI Receptionist business configuration..."
    
    if python3 seed_business_data.py; then
        success "Business data seeded successfully"
    else
        error "Failed to seed business data"
        return 1
    fi
}

# Start main application
start_application() {
    title "🚀 Starting AI Receptionist Application"
    
    log "Starting FastAPI backend..."
    
    # Start the main application
    docker-compose -f docker-compose.prod.yml up -d app
    
    # Wait for application to be ready
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -s http://localhost:8002/health >/dev/null 2>&1; then
            success "AI Receptionist backend is running"
            break
        fi
        
        log "Waiting for backend... (attempt $attempt/$max_attempts)"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    if [[ $attempt -gt $max_attempts ]]; then
        error "Backend failed to start within timeout"
        return 1
    fi
}

# Verify system health
verify_system() {
    title "🔍 System Verification"
    
    # Check all services are running
    log "Checking service status..."
    docker-compose -f docker-compose.prod.yml ps
    
    # Test database connection
    log "Testing database connection..."
    if docker-compose -f docker-compose.prod.yml exec -T postgres psql -U ai_receptionist_user -d ai_receptionist -c "SELECT 1;" >/dev/null 2>&1; then
        success "Database connection: OK"
    else
        error "Database connection: FAILED"
        return 1
    fi
    
    # Test API health
    log "Testing API health..."
    if curl -s http://localhost:8002/health | grep -q "healthy"; then
        success "API health check: OK"
    else
        error "API health check: FAILED"
        return 1
    fi
    
    # Test business data
    log "Verifying business data..."
    local business_count=$(docker-compose -f docker-compose.prod.yml exec -T postgres psql -U ai_receptionist_user -d ai_receptionist -t -c "SELECT COUNT(*) FROM businesses WHERE is_active = true;" | tr -d ' \n')
    
    if [[ "$business_count" -gt 0 ]]; then
        success "Business data: $business_count active business(es)"
    else
        warning "No active businesses found"
    fi
}

# Install backup cron job
setup_backups() {
    title "💾 Setting Up Automated Backups"
    
    if [[ -x "./backup_database.sh" ]]; then
        ./backup_database.sh install-cron
        success "Daily backups configured (2:00 AM)"
    else
        warning "Backup script not found or not executable"
    fi
}

# Display final status
show_status() {
    title "🎉 AI Receptionist Production System"
    
    echo "System Status:"
    echo "  🌐 Backend API: http://localhost:8002"
    echo "  🗄️  Database: PostgreSQL (persistent)"
    echo "  ⚡ Cache: Redis"
    echo "  🔍 Vector DB: Qdrant"
    echo ""
    echo "Next Steps:"
    echo "  1. Configure your domain to point to port 8002"
    echo "  2. Set up SSL/TLS with reverse proxy (Caddy/nginx)"
    echo "  3. Configure Twilio webhooks to your domain"
    echo "  4. Test phone number integration"
    echo ""
    echo "Useful Commands:"
    echo "  View logs:           docker-compose -f docker-compose.prod.yml logs -f"
    echo "  Stop system:         docker-compose -f docker-compose.prod.yml down"
    echo "  Backup database:     ./backup_database.sh manual"
    echo "  Restart system:      ./start_production.sh"
    echo ""
    success "AI Receptionist is ready for production! 🎊"
}

# Main execution
main() {
    local reset_data=false
    
    # Parse arguments
    for arg in "$@"; do
        case $arg in
            --reset-data)
                reset_data=true
                shift
                ;;
            *)
                echo "Usage: $0 [--reset-data]"
                exit 1
                ;;
        esac
    done
    
    echo "=================================================="
    echo "🤖 AI RECEPTIONIST PRODUCTION STARTUP"
    echo "   Time: $(date)"
    echo "   Mode: Production with PostgreSQL"
    if $reset_data; then
        echo "   ⚠️  RESET MODE: Will destroy existing data"
    fi
    echo "=================================================="
    
    # Confirm reset if requested
    if $reset_data; then
        echo -e "${RED}WARNING: --reset-data will destroy all existing data!${NC}"
        read -p "Are you sure? Type 'yes' to continue: " confirm
        if [[ "$confirm" != "yes" ]]; then
            echo "Cancelled."
            exit 0
        fi
        
        log "Stopping and removing existing containers..."
        docker-compose -f docker-compose.prod.yml down -v
        log "Existing data destroyed"
    fi
    
    # Execute startup sequence
    check_prerequisites
    create_directories
    setup_network
    start_services
    run_migrations
    seed_business_data
    start_application
    verify_system
    setup_backups
    show_status
}

# Trap cleanup on exit
cleanup() {
    if [[ $? -ne 0 ]]; then
        echo ""
        error "Startup failed. Check logs with:"
        echo "  docker-compose -f docker-compose.prod.yml logs"
    fi
}

trap cleanup EXIT

# Run main function
main "$@"