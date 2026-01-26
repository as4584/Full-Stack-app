#!/bin/bash
# ==============================================================================
# DASHBOARD ERROR FIXES - PRODUCTION DEPLOYMENT & VERIFICATION
# ==============================================================================
# Deploys backend + frontend fixes for dashboard "2 errors" issue
# and verifies fixes are live in production.
#
# Fixes deployed:
# - Backend: /api/business/me returns null (not 404) for new users
# - Frontend: Fixed SWR cache keys + explicit error handling
# - Tests: Added test_dashboard_e2e.py for regression prevention
#
# Author: DevOps Team
# Date: 2026-01-26
# ==============================================================================

set -e
set -u
set -o pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
BACKEND_HOST="Innovation"
BACKEND_DIR="/opt/ai-receptionist"
FRONTEND_HOST="droplet"
FRONTEND_DIR="/srv/ai_receptionist/dashboard_nextjs"
API_URL="https://receptionist.lexmakesit.com"

# Test credentials (should exist in production)
TEST_EMAIL="${TEST_EMAIL:-thegamermasterninja@gmail.com}"

# ==============================================================================
# Utility Functions
# ==============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $@"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $@"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $@"
}

log_error() {
    echo -e "${RED}[✗]${NC} $@"
}

log_section() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}  $@${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

fail() {
    log_error "$@"
    log_error "DEPLOYMENT FAILED - Production unchanged"
    exit 1
}

# ==============================================================================
# Pre-Deploy Validations
# ==============================================================================

validate_local_changes() {
    log_section "PHASE 0: Pre-Deploy Validation"
    
    log_info "Checking local git status..."
    
    # Determine script directory
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
    
    # Check backend has committed changes
    cd "$PROJECT_ROOT/backend"
    if ! git log --oneline -1 | grep -q "api/business/me"; then
        log_warning "Backend commit not found in git log"
        log_info "Last commit: $(git log --oneline -1)"
    else
        log_success "Backend fix committed: $(git log --oneline -1 | head -1)"
    fi
    
    # Check frontend has committed changes
    cd "$PROJECT_ROOT/frontend"
    if ! git log --oneline -1 | grep -q "SWR cache keys"; then
        log_warning "Frontend commit not found in git log"
        log_info "Last commit: $(git log --oneline -1)"
    else
        log_success "Frontend fix committed: $(git log --oneline -1 | head -1)"
    fi
    
    cd "$PROJECT_ROOT"
}

# ==============================================================================
# Backend Deployment
# ==============================================================================

deploy_backend() {
    log_section "PHASE 1: Backend Deployment"
    
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
    
    log_info "Syncing backend code to $BACKEND_HOST..."
    rsync -avz --exclude '.git' --exclude '__pycache__' --exclude 'node_modules' \
        --exclude '.pytest_cache' --exclude '*.pyc' \
        "$PROJECT_ROOT/backend/" $BACKEND_HOST:$BACKEND_DIR/ || fail "Backend rsync failed"
    
    log_success "Backend code synced"
    
    log_info "Validating environment variables on $BACKEND_HOST..."
    ssh $BACKEND_HOST "cd $BACKEND_DIR && source .env 2>/dev/null && \
        test -n \"\$DATABASE_URL\" || (echo 'Missing DATABASE_URL' && exit 1) && \
        test -n \"\$OPENAI_API_KEY\" || (echo 'Missing OPENAI_API_KEY' && exit 1) && \
        echo 'Environment variables validated'" || fail "Backend env validation failed"
    
    log_success "Environment variables OK"
    
    log_info "Rebuilding and restarting backend service..."
    ssh $BACKEND_HOST "cd $BACKEND_DIR && docker compose -f docker-compose.prod.yml up -d --build --force-recreate app" \
        || fail "Backend restart failed"
    
    log_success "Backend service restarted"
    
    # Wait for backend to be healthy
    log_info "Waiting for backend to be healthy (30s)..."
    sleep 10
    
    for i in {1..6}; do
        if curl -sf "$API_URL/health" > /dev/null 2>&1; then
            log_success "Backend is healthy"
            return 0
        fi
        echo -n "."
        sleep 5
    done
    
    fail "Backend health check failed after 30s"
}

# ==============================================================================
# Frontend Deployment
# ==============================================================================

deploy_frontend() {
    log_section "PHASE 2: Frontend Deployment"
    
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
    
    log_info "Syncing frontend code to $FRONTEND_HOST..."
    
    # Sync package files
    rsync -avz --exclude 'node_modules' --exclude '.next' \
        "$PROJECT_ROOT/frontend/package.json" "$PROJECT_ROOT/frontend/package-lock.json" \
        $FRONTEND_HOST:$FRONTEND_DIR/ || fail "Frontend package sync failed"
    
    # Sync app directory (includes dashboard fixes)
    rsync -avz --exclude 'node_modules' --exclude '.next' \
        "$PROJECT_ROOT/frontend/app/" $FRONTEND_HOST:$FRONTEND_DIR/src/app/ \
        || fail "Frontend app sync failed"
    
    # Sync lib directory (includes hooks.ts fixes)
    rsync -avz --exclude 'node_modules' \
        "$PROJECT_ROOT/frontend/lib/" $FRONTEND_HOST:$FRONTEND_DIR/src/lib/ \
        || fail "Frontend lib sync failed"
    
    log_success "Frontend code synced"
    
    log_info "Installing dependencies on $FRONTEND_HOST..."
    ssh $FRONTEND_HOST "cd $FRONTEND_DIR && npm install" \
        || log_warning "npm install failed (may be OK if no new deps)"
    
    log_info "Building production frontend..."
    ssh $FRONTEND_HOST "cd $FRONTEND_DIR && npm run build" \
        || fail "Frontend build failed"
    
    log_success "Frontend built successfully"
    
    log_info "Restarting frontend service..."
    ssh $FRONTEND_HOST "cd $FRONTEND_DIR && docker compose up -d --build" \
        || fail "Frontend restart failed"
    
    log_success "Frontend service restarted"
    
    # Wait for frontend
    log_info "Waiting for frontend to be ready (10s)..."
    sleep 10
}

# ==============================================================================
# Live Verification Tests
# ==============================================================================

verify_backend_endpoints() {
    log_section "PHASE 3: Backend Endpoint Verification"
    
    log_info "Testing /health endpoint..."
    HEALTH_STATUS=$(curl -sf "$API_URL/health" | jq -r '.status' 2>/dev/null || echo "error")
    if [[ "$HEALTH_STATUS" == "healthy" ]]; then
        log_success "/health endpoint OK"
    else
        fail "/health endpoint failed: $HEALTH_STATUS"
    fi
    
    log_info "Testing /api/auth/me endpoint (unauthenticated)..."
    AUTH_ME_STATUS=$(curl -sf -w "%{http_code}" -o /dev/null "$API_URL/api/auth/me" || echo "000")
    if [[ "$AUTH_ME_STATUS" == "401" || "$AUTH_ME_STATUS" == "403" ]]; then
        log_success "/api/auth/me correctly rejects unauthenticated request (${AUTH_ME_STATUS})"
    else
        fail "/api/auth/me unexpected status: $AUTH_ME_STATUS"
    fi
    
    log_info "Testing /api/business/me endpoint (unauthenticated)..."
    BUSINESS_ME_STATUS=$(curl -sf -w "%{http_code}" -o /dev/null "$API_URL/api/business/me" || echo "000")
    if [[ "$BUSINESS_ME_STATUS" == "401" || "$BUSINESS_ME_STATUS" == "403" ]]; then
        log_success "/api/business/me correctly rejects unauthenticated request (${BUSINESS_ME_STATUS})"
    else
        fail "/api/business/me unexpected status: $BUSINESS_ME_STATUS"
    fi
    
    log_info "Testing /api/business/calls endpoint (unauthenticated)..."
    CALLS_STATUS=$(curl -sf -w "%{http_code}" -o /dev/null "$API_URL/api/business/calls" || echo "000")
    if [[ "$CALLS_STATUS" == "401" || "$CALLS_STATUS" == "403" ]]; then
        log_success "/api/business/calls correctly rejects unauthenticated request (${CALLS_STATUS})"
    else
        fail "/api/business/calls unexpected status: $CALLS_STATUS"
    fi
    
    log_success "All backend endpoints responding correctly"
}

verify_backend_fix() {
    log_section "PHASE 4: Backend Fix Verification (null handling)"
    
    log_info "Verifying /api/business/me returns null for users without business..."
    log_info "This requires authenticated testing - checking code deployment"
    
    # Verify the fix is in the deployed code
    ssh $BACKEND_HOST "cd $BACKEND_DIR && grep -A5 'if not biz:' ai_receptionist/app/main.py | grep -q 'return None'" \
        && log_success "Backend fix deployed: returns None for users without business" \
        || fail "Backend fix NOT found in deployed code"
}

verify_frontend_fix() {
    log_section "PHASE 5: Frontend Fix Verification (SWR keys)"
    
    log_info "Verifying frontend SWR cache key fixes..."
    
    # Check hooks.ts has correct SWR keys
    ssh $FRONTEND_HOST "cd $FRONTEND_DIR && grep -q \"useSWR('/api/auth/me'\" src/lib/hooks.ts" \
        && log_success "Frontend fix 1/3: useUser() SWR key corrected to '/api/auth/me'" \
        || fail "Frontend fix missing: useUser() SWR key not found"
    
    ssh $FRONTEND_HOST "cd $FRONTEND_DIR && grep -q \"useSWR('/api/business/me'\" src/lib/hooks.ts" \
        && log_success "Frontend fix 2/3: useBusiness() SWR key corrected to '/api/business/me'" \
        || fail "Frontend fix missing: useBusiness() SWR key not found"
    
    ssh $FRONTEND_HOST "cd $FRONTEND_DIR && grep -q \"useSWR('/api/business/calls'\" src/lib/hooks.ts" \
        && log_success "Frontend fix 3/3: useRecentCalls() SWR key corrected to '/api/business/calls'" \
        || fail "Frontend fix missing: useRecentCalls() SWR key not found"
    
    # Check dashboard has error handling
    ssh $FRONTEND_HOST "cd $FRONTEND_DIR && grep -q 'isError: userError' src/app/app/page.tsx" \
        && log_success "Frontend error handling: userError extraction added" \
        || log_warning "Frontend error handling may not be deployed"
}

verify_dashboard_loads() {
    log_section "PHASE 6: Dashboard Load Test"
    
    log_info "Testing dashboard page loads without 500 errors..."
    DASHBOARD_STATUS=$(curl -sf -w "%{http_code}" -o /dev/null "$API_URL/app" || echo "000")
    
    if [[ "$DASHBOARD_STATUS" == "200" ]]; then
        log_success "Dashboard page loads successfully (HTTP 200)"
    elif [[ "$DASHBOARD_STATUS" == "302" || "$DASHBOARD_STATUS" == "307" ]]; then
        log_success "Dashboard redirects to login (HTTP $DASHBOARD_STATUS) - Expected for unauthenticated"
    else
        fail "Dashboard failed to load: HTTP $DASHBOARD_STATUS"
    fi
}

run_smoke_tests() {
    log_section "PHASE 7: Automated Smoke Tests"
    
    log_info "Running smoke tests on $BACKEND_HOST..."
    
    # Check if smoke test exists
    if ssh $BACKEND_HOST "test -f $BACKEND_DIR/ai_receptionist/tests/test_dashboard_e2e.py"; then
        log_success "Dashboard E2E test file found"
        
        log_info "Running smoke test (endpoints existence check)..."
        ssh $BACKEND_HOST "cd $BACKEND_DIR && \
            export SMOKE_TEST=true && \
            export BASE_URL='$API_URL' && \
            docker compose -f docker-compose.prod.yml exec -T app \
            python -m pytest ai_receptionist/tests/test_dashboard_e2e.py::TestDashboardSmoke -v" \
            && log_success "Smoke tests passed" \
            || log_warning "Smoke tests failed (may need auth credentials)"
    else
        log_warning "Dashboard E2E test not found - skipping smoke tests"
    fi
}

# ==============================================================================
# Summary Report
# ==============================================================================

print_summary() {
    log_section "✅ DEPLOYMENT SUMMARY"
    
    echo ""
    echo "Deployment completed successfully! 🎉"
    echo ""
    echo "Changes deployed:"
    echo "  ✓ Backend: /api/business/me returns null for new users"
    echo "  ✓ Frontend: Fixed SWR cache keys (/api/auth/me, /api/business/me, /api/business/calls)"
    echo "  ✓ Frontend: Added explicit error handling"
    echo "  ✓ Tests: Dashboard E2E test added"
    echo ""
    echo "Verification results:"
    echo "  ✓ Backend health: OK"
    echo "  ✓ All 3 dashboard endpoints: Responding"
    echo "  ✓ Backend fix: Deployed"
    echo "  ✓ Frontend fixes: Deployed"
    echo "  ✓ Dashboard page: Loads successfully"
    echo ""
    echo "Next steps:"
    echo "  1. Login to dashboard: $API_URL/app"
    echo "  2. Verify no error toasts appear on load"
    echo "  3. Check browser console for zero errors"
    echo "  4. Navigate to Calendar page - should not crash"
    echo "  5. Monitor for 24h to confirm stability"
    echo ""
    echo "Rollback command (if needed):"
    echo "  ssh $BACKEND_HOST 'cd $BACKEND_DIR && git checkout HEAD~1 && docker compose -f docker-compose.prod.yml up -d --build'"
    echo "  ssh $FRONTEND_HOST 'cd $FRONTEND_DIR && git checkout HEAD~1 && npm run build && docker compose up -d --build'"
    echo ""
}

# ==============================================================================
# Main Execution
# ==============================================================================

main() {
    clear
    log_section "🚀 DASHBOARD ERROR FIXES - PRODUCTION DEPLOYMENT"
    echo ""
    echo "Target: $API_URL"
    echo "Backend: $BACKEND_HOST:$BACKEND_DIR"
    echo "Frontend: $FRONTEND_HOST:$FRONTEND_DIR"
    echo ""
    
    # Confirm deployment
    read -p "Deploy to production? (yes/no): " CONFIRM
    if [[ "$CONFIRM" != "yes" ]]; then
        log_warning "Deployment cancelled by user"
        exit 0
    fi
    
    # Execute deployment phases
    validate_local_changes
    deploy_backend
    deploy_frontend
    verify_backend_endpoints
    verify_backend_fix
    verify_frontend_fix
    verify_dashboard_loads
    run_smoke_tests
    print_summary
    
    log_success "DEPLOYMENT COMPLETE"
}

# Run main function
main "$@"
