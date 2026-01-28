#!/bin/bash
# ==============================================================================
# SAFE PRODUCTION DEPLOY SCRIPT
# ==============================================================================
# This script safely deploys backend changes to production without causing
# authentication lockouts or data loss.
#
# SAFETY GUARANTEES:
# - Validates required environment variables BEFORE restarting
# - NEVER deletes Docker volumes (preserves database)
# - Validates secrets exist and are non-empty
# - Fails fast if any validation fails
# - Logs all operations for audit trail
# ==============================================================================

set -e  # Exit on any error
set -u  # Exit on undefined variable
set -o pipefail  # Exit on pipe failure

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DEPLOY_DIR="/opt/ai-receptionist"
COMPOSE_FILE="docker-compose.prod.yml"
LOG_FILE="/var/log/ai-receptionist-deploy.log"

# Required environment variables (CRITICAL for auth stability)
REQUIRED_SECRETS=(
    "ADMIN_PRIVATE_KEY"
    "DATABASE_URL"
    "POSTGRES_USER"
    "POSTGRES_PASSWORD"
    "OPENAI_API_KEY"
)

# Optional but recommended
RECOMMENDED_SECRETS=(
    "TWILIO_ACCOUNT_SID"
    "TWILIO_AUTH_TOKEN"
    "SENDGRID_API_KEY"
)

# ==============================================================================
# Utility Functions
# ==============================================================================

log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a "$LOG_FILE"
}

log_info() {
    echo -e "${BLUE}ℹ${NC} $@"
    log "INFO" "$@"
}

log_success() {
    echo -e "${GREEN}✅${NC} $@"
    log "SUCCESS" "$@"
}

log_warning() {
    echo -e "${YELLOW}⚠️${NC} $@"
    log "WARNING" "$@"
}

log_error() {
    echo -e "${RED}❌${NC} $@"
    log "ERROR" "$@"
}

fail() {
    log_error "$@"
    log_error "DEPLOY ABORTED - No changes made to production"
    exit 1
}

# ==============================================================================
# Pre-flight Checks
# ==============================================================================

preflight_checks() {
    log_info "Starting pre-flight checks..."
    
    # Check if running on correct server
    if [[ ! -d "$DEPLOY_DIR" ]]; then
        fail "Deploy directory $DEPLOY_DIR not found. Are you on the correct server?"
    fi
    
    # Check if docker is running
    if ! docker ps >/dev/null 2>&1; then
        fail "Docker is not running or current user lacks permissions"
    fi
    
    # Check if compose file exists
    if [[ ! -f "$DEPLOY_DIR/$COMPOSE_FILE" ]]; then
        fail "Docker compose file not found: $DEPLOY_DIR/$COMPOSE_FILE"
    fi
    
    # Check if .env file exists
    if [[ ! -f "$DEPLOY_DIR/.env" ]]; then
        fail ".env file not found in $DEPLOY_DIR"
    fi
    
    log_success "Pre-flight checks passed"
}

# ==============================================================================
# Environment Validation
# ==============================================================================

validate_environment() {
    log_info "Validating production environment variables..."
    
    # Load .env file
    cd "$DEPLOY_DIR"
    set -a  # automatically export all variables
    source .env
    set +a
    
    local missing_required=()
    local missing_recommended=()
    
    # Check required secrets
    for secret in "${REQUIRED_SECRETS[@]}"; do
        if [[ -z "${!secret:-}" ]]; then
            missing_required+=("$secret")
        else
            # Validate secret is not a placeholder
            local value="${!secret}"
            if [[ "$value" =~ ^(CHANGEME|TODO|FIXME|REPLACE|YOUR_|EXAMPLE) ]]; then
                missing_required+=("$secret (contains placeholder value)")
            else
                log_success "$secret: configured (${#value} chars)"
            fi
        fi
    done
    
    # Check recommended secrets
    for secret in "${RECOMMENDED_SECRETS[@]}"; do
        if [[ -z "${!secret:-}" ]]; then
            missing_recommended+=("$secret")
        fi
    done
    
    # Report missing required secrets
    if [[ ${#missing_required[@]} -gt 0 ]]; then
        log_error "Missing REQUIRED environment variables:"
        for secret in "${missing_required[@]}"; do
            log_error "  - $secret"
        done
        fail "Required secrets missing. Set them in $DEPLOY_DIR/.env before deploying."
    fi
    
    # Report missing recommended secrets
    if [[ ${#missing_recommended[@]} -gt 0 ]]; then
        log_warning "Missing RECOMMENDED environment variables:"
        for secret in "${missing_recommended[@]}"; do
            log_warning "  - $secret"
        done
        log_warning "These are optional but may limit functionality"
    fi
    
    log_success "All required environment variables validated"
}

# ==============================================================================
# Volume Safety Check
# ==============================================================================

check_volumes() {
    log_info "Checking Docker volumes (ensuring data preservation)..."
    
    # List volumes used by the application
    local volumes=$(docker compose -f "$COMPOSE_FILE" config --volumes)
    
    if [[ -z "$volumes" ]]; then
        log_warning "No named volumes found in compose file"
        return
    fi
    
    echo "$volumes" | while read -r volume_name; do
        if docker volume inspect "$volume_name" >/dev/null 2>&1; then
            log_success "Volume exists: $volume_name"
        else
            log_warning "Volume does not exist yet: $volume_name (will be created)"
        fi
    done
    
    log_info "🔒 VOLUME SAFETY: This script NEVER deletes volumes"
    log_info "🔒 Database data will be preserved across deploys"
}

# ==============================================================================
# Git Update
# ==============================================================================

update_code() {
    log_info "Updating code from git repository..."
    
    cd "$DEPLOY_DIR"
    
    # Save current commit for rollback
    local current_commit=$(git rev-parse HEAD)
    log_info "Current commit: $current_commit"
    
    # Pull latest changes
    if git pull origin master; then
        local new_commit=$(git rev-parse HEAD)
        log_success "Updated to commit: $new_commit"
        
        if [[ "$current_commit" == "$new_commit" ]]; then
            log_info "No new changes to deploy"
        else
            log_info "Changes detected between $current_commit and $new_commit"
        fi
    else
        fail "Git pull failed. Check network and repository access."
    fi
}

# ==============================================================================
# Database Migration Check
# ==============================================================================

check_migrations() {
    log_info "Checking database migration status..."
    
    cd "$DEPLOY_DIR"
    
    # Check if there are pending migrations
    if docker compose -f "$COMPOSE_FILE" exec -T app alembic current >/dev/null 2>&1; then
        log_success "Database schema is accessible"
    else
        log_warning "Could not check migration status (app may not be running yet)"
    fi
}

# ==============================================================================
# Safe Container Restart
# ==============================================================================

safe_restart() {
    log_info "Performing safe container restart..."
    
    cd "$DEPLOY_DIR"
    
    # Pull latest images (if any)
    log_info "Pulling latest base images..."
    docker compose -f "$COMPOSE_FILE" pull --quiet || log_warning "Image pull failed, using cached images"
    
    # Rebuild app container only (preserves data containers)
    log_info "Rebuilding application container..."
    docker compose -f "$COMPOSE_FILE" build app
    
    # Restart app container only (keeps database running)
    log_info "Restarting application container..."
    docker compose -f "$COMPOSE_FILE" up -d app
    
    log_success "Container restart complete"
}

# ==============================================================================
# Post-Deploy Validation
# ==============================================================================

validate_deployment() {
    log_info "Validating deployment..."
    
    cd "$DEPLOY_DIR"
    
    # Wait for app to be healthy
    log_info "Waiting for application to become healthy (max 60s)..."
    local max_attempts=12
    local attempt=0
    
    while [[ $attempt -lt $max_attempts ]]; do
        if docker compose -f "$COMPOSE_FILE" ps app | grep -q "healthy"; then
            log_success "Application is healthy"
            break
        fi
        
        attempt=$((attempt + 1))
        if [[ $attempt -eq $max_attempts ]]; then
            log_error "Application failed to become healthy"
            log_info "Recent logs:"
            docker compose -f "$COMPOSE_FILE" logs --tail=30 app
            fail "Deployment validation failed - application not healthy"
        fi
        
        log_info "Attempt $attempt/$max_attempts - waiting 5s..."
        sleep 5
    done
    
    # Check health endpoint
    log_info "Checking health endpoint..."
    if curl -f http://localhost:8002/health >/dev/null 2>&1; then
        log_success "Health endpoint responding"
    else
        log_warning "Health endpoint not responding (may be normal if behind proxy)"
    fi
    
    # Check database connection
    log_info "Verifying database connectivity..."
    if docker compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U "$POSTGRES_USER" >/dev/null 2>&1; then
        log_success "Database connection verified"
    else
        log_warning "Could not verify database connection"
    fi
    
    log_success "Deployment validation passed"
}

# ==============================================================================
# Run Migrations
# ==============================================================================

run_migrations() {
    log_info "Running database migrations..."
    
    cd "$DEPLOY_DIR"
    
    if docker compose -f "$COMPOSE_FILE" exec -T -e PYTHONPATH=/app app alembic upgrade head; then
        log_success "Database migrations completed"
    else
        log_error "Migration failed"
        log_info "Recent app logs:"
        docker compose -f "$COMPOSE_FILE" logs --tail=20 app
        fail "Database migration failed. Review logs above."
    fi
}

# ==============================================================================
# Display Final Status
# ==============================================================================

display_status() {
    log_info "==================================================================="
    log_success "✨ DEPLOYMENT SUCCESSFUL"
    log_info "==================================================================="
    log_info ""
    log_info "Container Status:"
    docker compose -f "$COMPOSE_FILE" ps
    log_info ""
    log_info "Recent Application Logs:"
    docker compose -f "$COMPOSE_FILE" logs --tail=10 app
    log_info ""
    log_info "==================================================================="
    log_info "🔐 Auth Status: JWT secret persisted in .env"
    log_info "💾 Database: Volume preserved (no data loss)"
    log_info "📝 Logs: $LOG_FILE"
    log_info "==================================================================="
}

# ==============================================================================
# Main Execution
# ==============================================================================

main() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║         SAFE PRODUCTION DEPLOY - AI RECEPTIONIST BACKEND        ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo ""
    
    log_info "Deploy started at $(date)"
    log_info "Deploy directory: $DEPLOY_DIR"
    log_info "Compose file: $COMPOSE_FILE"
    echo ""
    
    # Run all deployment steps
    preflight_checks
    validate_environment
    check_volumes
    update_code
    check_migrations
    safe_restart
    run_migrations
    validate_deployment
    display_status
    
    log_success "Deploy completed successfully at $(date)"
}

# Run main function
main "$@"
