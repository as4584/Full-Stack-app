#!/bin/bash
################################################################################
# BACKEND POST-DEPLOY VERIFICATION
################################################################################
#
# PURPOSE:
#   Verify backend API health after deployment to production.
#   Runs smoke tests against LIVE backend API to ensure core functionality.
#
# MULTI-REPO ARCHITECTURE:
#   - This script ONLY verifies backend API correctness
#   - Frontend deployment is separate and not assumed
#   - Backend must be healthy independently
#
# USAGE:
#   ./backend_post_deploy_verify.sh [API_URL]
#
#   API_URL defaults to https://receptionist.lexmakesit.com
#
# EXIT CODES:
#   0 - All backend API tests passed
#   1 - Settings API failed
#   2 - Calendar API failed
#   3 - Twilio API failed
#   4 - Multiple APIs failed
#   5 - Script error (missing dependencies, etc.)
#
# INTEGRATION WITH DEPLOY PIPELINE:
#   
#   # In your backend deploy script:
#   
#   # 1. Deploy backend code
#   docker compose -f docker-compose.prod.yml up -d --build
#   
#   # 2. Wait for backend to start
#   sleep 30
#   
#   # 3. Verify backend API health
#   ./backend_post_deploy_verify.sh || {
#       echo "❌ BACKEND API VERIFICATION FAILED"
#       echo "Backend is NOT healthy - consider rollback"
#       exit 1
#   }
#   
#   echo "✅ Backend API verified and healthy"
#
################################################################################

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Configuration
API_URL="${1:-https://receptionist.lexmakesit.com}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

log_header() {
    echo -e "${CYAN}[BACKEND]${NC} $*"
}

# Print header
print_header() {
    echo ""
    echo "================================================================================"
    echo "                   BACKEND POST-DEPLOY VERIFICATION"
    echo "================================================================================"
    echo "API URL: $API_URL"
    echo "Mode: SMOKE TEST (fast API verification)"
    echo "Time: $(date -Iseconds)"
    echo "Architecture: Backend-only (frontend deployment is separate)"
    echo "================================================================================"
    echo ""
}

# Check prerequisites
check_prerequisites() {
    log_header "Checking prerequisites..."
    
    if ! command -v python3 &> /dev/null; then
        log_error "python3 not found - required for running API tests"
        exit 5
    fi
    
    if ! python3 -c "import requests" &> /dev/null; then
        log_error "Python 'requests' module not found"
        log_info "Install with: pip3 install requests"
        exit 5
    fi
    
    if ! python3 -c "import bcrypt" &> /dev/null; then
        log_warning "Python 'bcrypt' module not found (may be needed for auth tests)"
        log_info "Install with: pip3 install bcrypt"
    fi
    
    # Check if test scripts exist
    local required_tests=(
        "test_settings_e2e.py"
        "test_calendar_e2e.py"
        "test_twilio_e2e.py"
    )
    
    for test_file in "${required_tests[@]}"; do
        if [ ! -f "$SCRIPT_DIR/$test_file" ]; then
            log_error "Test script not found: $SCRIPT_DIR/$test_file"
            exit 5
        fi
    done
    
    log_success "Prerequisites OK"
}

# Run a single smoke test against backend API
run_api_smoke_test() {
    local test_name="$1"
    local test_script="$2"
    local exit_code_var="$3"
    
    log_header "Testing ${test_name} API..."
    
    cd "$SCRIPT_DIR" || exit 5
    
    # Run test with timeout (30 seconds for smoke tests)
    if timeout 30s env SMOKE_TEST=true python3 "$test_script" --url "$API_URL" > "/tmp/backend_${test_name}_smoke.log" 2>&1; then
        log_success "${test_name} API is healthy"
        eval "$exit_code_var=0"
    else
        local exit_code=$?
        log_error "${test_name} API test FAILED (exit code: $exit_code)"
        log_info "Last 20 lines of output:"
        tail -20 "/tmp/backend_${test_name}_smoke.log" | sed 's/^/  /'
        eval "$exit_code_var=$exit_code"
    fi
}

# Main function
main() {
    print_header
    check_prerequisites
    
    # Track individual API test results
    local exit_settings=0
    local exit_calendar=0
    local exit_twilio=0
    
    log_info "Verifying backend APIs (smoke tests run sequentially)..."
    echo ""
    
    # Run API smoke tests
    run_api_smoke_test "Settings" "test_settings_e2e.py" "exit_settings"
    run_api_smoke_test "Calendar" "test_calendar_e2e.py" "exit_calendar"
    run_api_smoke_test "Twilio" "test_twilio_e2e.py" "exit_twilio"
    
    # Summary
    echo ""
    echo "================================================================================"
    echo "                      BACKEND API VERIFICATION SUMMARY"
    echo "================================================================================"
    
    # Check results
    local failed_count=0
    
    if [ $exit_settings -ne 0 ]; then
        log_error "Settings API: FAILED (exit $exit_settings)"
        echo "  - Critical: Settings save/fetch is broken"
        ((failed_count++))
    else
        log_success "Settings API: PASSED"
    fi
    
    if [ $exit_calendar -ne 0 ]; then
        log_error "Calendar API: FAILED (exit $exit_calendar)"
        echo "  - Calendar OAuth or state endpoint is broken"
        ((failed_count++))
    else
        log_success "Calendar API: PASSED"
    fi
    
    if [ $exit_twilio -ne 0 ]; then
        log_error "Twilio API: FAILED (exit $exit_twilio)"
        echo "  - Phone number or receptionist API is broken"
        ((failed_count++))
    else
        log_success "Twilio API: PASSED"
    fi
    
    echo "================================================================================"
    echo ""
    
    # Determine exit code
    if [ $failed_count -eq 0 ]; then
        log_success "✅ ALL BACKEND API TESTS PASSED"
        log_info "Backend is healthy and ready for traffic"
        log_info ""
        log_info "Note: Frontend deployment is separate. This verifies backend only."
        return 0
    elif [ $failed_count -ge 2 ]; then
        log_error "❌ MULTIPLE BACKEND API FAILURES ($failed_count/3)"
        log_error "Backend has CRITICAL issues - IMMEDIATE ACTION REQUIRED"
        log_warning "Strongly consider rolling back this deployment"
        return 4
    else
        log_error "❌ ONE BACKEND API FAILURE"
        log_warning "Backend is partially broken - investigate immediately"
        
        # Return specific exit code based on which API failed
        if [ $exit_settings -ne 0 ]; then
            return 1
        elif [ $exit_calendar -ne 0 ]; then
            return 2
        else
            return 3
        fi
    fi
}

# Run main function
main "$@"
exit $?
