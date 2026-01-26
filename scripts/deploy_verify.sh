#!/bin/bash
###############################################################################
# Post-Deploy Verification Script
###############################################################################
#
# Runs smoke tests after deployment to verify core functionality.
# Designed to be called automatically after `docker compose up -d` in
# production deployments.
#
# USAGE:
#   ./deploy_verify.sh [API_URL]
#
#   API_URL defaults to https://receptionist.lexmakesit.com if not provided
#
# EXIT CODES:
#   0 - All smoke tests passed
#   1 - Settings smoke test failed
#   2 - Calendar smoke test failed
#   3 - Twilio smoke test failed
#   4 - Multiple tests failed
#   5 - Script error (missing dependencies, etc.)
#
# INTEGRATION:
#   Add to your deploy script after `docker compose up -d`:
#   
#   ./deploy_verify.sh || {
#       echo "❌ Post-deploy verification FAILED"
#       echo "Consider rolling back deployment"
#       exit 1
#   }
#
###############################################################################

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Configuration
API_URL="${1:-https://receptionist.lexmakesit.com}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TEST_DIR="${PROJECT_ROOT}/backend"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Print header
print_header() {
    echo ""
    echo "================================================================================"
    echo "                    POST-DEPLOY VERIFICATION"
    echo "================================================================================"
    echo "API URL: $API_URL"
    echo "Mode: SMOKE TEST (fast verification)"
    echo "Time: $(date -Iseconds)"
    echo "================================================================================"
    echo ""
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v python3 &> /dev/null; then
        log_error "python3 not found - required for running tests"
        exit 5
    fi
    
    if ! python3 -c "import requests" &> /dev/null; then
        log_error "Python 'requests' module not found"
        log_info "Install with: pip3 install requests"
        exit 5
    fi
    
    if ! python3 -c "import bcrypt" &> /dev/null; then
        log_warning "Python 'bcrypt' module not found (may be needed for some tests)"
        log_info "Install with: pip3 install bcrypt"
    fi
    
    if [ ! -d "$TEST_DIR" ]; then
        log_error "Test directory not found: $TEST_DIR"
        exit 5
    fi
    
    log_success "Prerequisites OK"
}

# Run a single smoke test
run_smoke_test() {
    local test_name="$1"
    local test_script="$2"
    local exit_code_var="$3"
    
    log_info "Running ${test_name} smoke test..."
    
    cd "$TEST_DIR" || exit 5
    
    if [ ! -f "$test_script" ]; then
        log_error "Test script not found: $test_script"
        eval "$exit_code_var=5"
        return
    fi
    
    # Run test with timeout (30 seconds for smoke tests)
    if timeout 30s env SMOKE_TEST=true python3 "$test_script" --url "$API_URL" > "/tmp/${test_name}_smoke.log" 2>&1; then
        log_success "${test_name} smoke test PASSED"
        eval "$exit_code_var=0"
    else
        local exit_code=$?
        log_error "${test_name} smoke test FAILED (exit code: $exit_code)"
        log_info "Last 20 lines of output:"
        tail -20 "/tmp/${test_name}_smoke.log" | sed 's/^/  /'
        eval "$exit_code_var=$exit_code"
    fi
}

# Main function
main() {
    print_header
    check_prerequisites
    
    # Track individual test results
    local exit_settings=0
    local exit_calendar=0
    local exit_twilio=0
    
    # Run tests sequentially (fast enough with smoke mode)
    run_smoke_test "Settings" "test_settings_e2e.py" "exit_settings"
    run_smoke_test "Calendar" "test_calendar_e2e.py" "exit_calendar"
    run_smoke_test "Twilio" "test_twilio_e2e.py" "exit_twilio"
    
    # Summary
    echo ""
    echo "================================================================================"
    echo "                         VERIFICATION SUMMARY"
    echo "================================================================================"
    
    # Check results
    local failed_count=0
    
    if [ $exit_settings -ne 0 ]; then
        log_error "Settings: FAILED (exit $exit_settings)"
        ((failed_count++))
    else
        log_success "Settings: PASSED"
    fi
    
    if [ $exit_calendar -ne 0 ]; then
        log_error "Calendar: FAILED (exit $exit_calendar)"
        ((failed_count++))
    else
        log_success "Calendar: PASSED"
    fi
    
    if [ $exit_twilio -ne 0 ]; then
        log_error "Twilio: FAILED (exit $exit_twilio)"
        ((failed_count++))
    else
        log_success "Twilio: PASSED"
    fi
    
    echo "================================================================================"
    echo ""
    
    # Determine exit code
    if [ $failed_count -eq 0 ]; then
        log_success "✅ ALL POST-DEPLOY VERIFICATION TESTS PASSED"
        log_info "Deployment is healthy and ready for traffic"
        return 0
    elif [ $failed_count -ge 2 ]; then
        log_error "❌ MULTIPLE VERIFICATION TESTS FAILED ($failed_count/3)"
        log_error "Deployment may have critical issues - consider rollback"
        return 4
    else
        log_error "❌ ONE VERIFICATION TEST FAILED"
        log_warning "Deployment may be partially working - investigate immediately"
        
        # Return specific exit code based on which test failed
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
