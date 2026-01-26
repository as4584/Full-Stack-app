#!/bin/bash
#
# Main CI Auth Test Runner
# Orchestrates all phases of authentication testing.
#

set -e  # Exit on any error

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TEST_DIR="$PROJECT_ROOT/tests/ci-auth"
PYTHON="python3"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_step() {
    echo -e "${BLUE}🔄 $1${NC}"
}

# Help function
show_help() {
    cat << EOF
🔐 CI Auth Test Suite

USAGE:
    $0 [OPTIONS] [PHASES]

OPTIONS:
    --help, -h          Show this help message
    --create-baseline   Create new regression baseline (Phase 4)
    --skip-cleanup      Don't clean up Docker containers after tests
    --verbose, -v       Verbose output

PHASES:
    all                 Run all phases (default)
    phase1             Static contract validation only
    phase2             Runtime smoke tests only  
    phase3             CORS & transport tests only
    phase4             Regression snapshot tests only

EXAMPLES:
    $0                        # Run all phases
    $0 phase1 phase2          # Run phases 1 and 2 only
    $0 --create-baseline      # Create new regression baseline
    $0 phase4 --verbose       # Run regression tests with verbose output

DESCRIPTION:
    This test suite ensures authentication never silently breaks by running:
    
    Phase 1: Static Contract Validation
    - Frontend/backend API contract matching
    - Environment variable validation
    - Hardcoded URL detection
    
    Phase 2: Runtime Auth Smoke Tests  
    - Docker compose service startup
    - End-to-end login flow testing
    - Token validation
    
    Phase 3: CORS & Transport Check
    - OPTIONS preflight testing
    - Origin validation 
    - Credentials handling
    
    Phase 4: Regression Snapshot
    - Baseline request/response capture
    - Breaking change detection
    - Diff reporting
EOF
}

# Parse arguments
PHASES=()
CREATE_BASELINE=false
SKIP_CLEANUP=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_help
            exit 0
            ;;
        --create-baseline)
            CREATE_BASELINE=true
            shift
            ;;
        --skip-cleanup)
            SKIP_CLEANUP=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        phase1|phase2|phase3|phase4|all)
            PHASES+=("$1")
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Default to all phases if none specified
if [[ ${#PHASES[@]} -eq 0 ]]; then
    PHASES=("all")
fi

# Check dependencies
check_dependencies() {
    log_step "Checking dependencies..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "python3 is required but not installed"
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "docker is required but not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "docker-compose is required but not installed"
        exit 1
    fi
    
    # Install Python dependencies if needed
    if [[ ! -f "$TEST_DIR/.deps_installed" ]]; then
        log_step "Installing Python dependencies..."
        pip3 install --quiet aiohttp docker pyyaml || {
            log_error "Failed to install Python dependencies"
            exit 1
        }
        touch "$TEST_DIR/.deps_installed"
    fi
    
    log_success "All dependencies satisfied"
}

# Run Phase 1: Static Contract Validation
run_phase1() {
    log_info "🔍 PHASE 1: Static Contract Validation"
    echo "════════════════════════════════════════════"
    
    $PYTHON "$TEST_DIR/phase1_contract_validator.py" "$PROJECT_ROOT"
    local phase1_result=$?
    
    if [[ $phase1_result -eq 0 ]]; then
        log_success "Phase 1: PASSED"
        return 0
    else
        log_error "Phase 1: FAILED"
        return 1
    fi
}

# Run Phase 2: Runtime Smoke Tests
run_phase2() {
    log_info "🧪 PHASE 2: Runtime Auth Smoke Tests"
    echo "════════════════════════════════════════════"
    
    $PYTHON "$TEST_DIR/phase2_runtime_smoke_test.py" "$PROJECT_ROOT"
    local phase2_result=$?
    
    if [[ $phase2_result -eq 0 ]]; then
        log_success "Phase 2: PASSED"
        return 0
    else
        log_error "Phase 2: FAILED"
        return 1
    fi
}

# Run Phase 3: CORS & Transport Tests
run_phase3() {
    log_info "🌐 PHASE 3: CORS & Transport Check"
    echo "════════════════════════════════════════════"
    
    $PYTHON "$TEST_DIR/phase3_cors_transport_test.py" "$PROJECT_ROOT"
    local phase3_result=$?
    
    if [[ $phase3_result -eq 0 ]]; then
        log_success "Phase 3: PASSED"
        return 0
    else
        log_error "Phase 3: FAILED"
        return 1
    fi
}

# Run Phase 4: Regression Snapshot
run_phase4() {
    log_info "📸 PHASE 4: Regression Snapshot Test"
    echo "════════════════════════════════════════════"
    
    local args=("$PROJECT_ROOT")
    if [[ "$CREATE_BASELINE" == true ]]; then
        args+=("--create-baseline")
    fi
    
    $PYTHON "$TEST_DIR/phase4_regression_snapshot.py" "${args[@]}"
    local phase4_result=$?
    
    if [[ $phase4_result -eq 0 ]]; then
        log_success "Phase 4: PASSED"
        return 0
    else
        log_error "Phase 4: FAILED"
        return 1
    fi
}

# Cleanup function
cleanup() {
    if [[ "$SKIP_CLEANUP" == false ]]; then
        log_step "Cleaning up test environment..."
        cd "$TEST_DIR"
        docker-compose -f docker-compose.ci.yml -p ci-auth-test down -v &> /dev/null || true
        log_success "Cleanup complete"
    fi
}

# Trap cleanup on exit
trap cleanup EXIT

# Main execution
main() {
    echo "🔐 AI Receptionist Auth CI Test Suite"
    echo "========================================"
    echo ""
    
    # Check dependencies
    check_dependencies
    
    # Track results
    declare -A phase_results
    local overall_success=true
    
    # Determine which phases to run
    local phases_to_run=()
    if [[ " ${PHASES[@]} " =~ " all " ]]; then
        phases_to_run=("phase1" "phase2" "phase3" "phase4")
    else
        phases_to_run=("${PHASES[@]}")
    fi
    
    # Run specified phases
    for phase in "${phases_to_run[@]}"; do
        echo ""
        case "$phase" in
            "phase1")
                if run_phase1; then
                    phase_results["phase1"]="PASSED"
                else
                    phase_results["phase1"]="FAILED"
                    overall_success=false
                fi
                ;;
            "phase2")
                if run_phase2; then
                    phase_results["phase2"]="PASSED"
                else
                    phase_results["phase2"]="FAILED"
                    overall_success=false
                fi
                ;;
            "phase3")
                if run_phase3; then
                    phase_results["phase3"]="PASSED"
                else
                    phase_results["phase3"]="FAILED"
                    overall_success=false
                fi
                ;;
            "phase4")
                if run_phase4; then
                    phase_results["phase4"]="PASSED"
                else
                    phase_results["phase4"]="FAILED"
                    overall_success=false
                fi
                ;;
        esac
    done
    
    # Final summary
    echo ""
    echo "📊 FINAL SUMMARY"
    echo "================"
    
    for phase in "${phases_to_run[@]}"; do
        if [[ "${phase_results[$phase]}" == "PASSED" ]]; then
            log_success "$phase: ${phase_results[$phase]}"
        else
            log_error "$phase: ${phase_results[$phase]}"
        fi
    done
    
    echo ""
    if [[ "$overall_success" == true ]]; then
        log_success "🎉 ALL TESTS PASSED - Authentication reliability verified!"
        exit 0
    else
        log_error "🚨 TESTS FAILED - Authentication has regressions or issues!"
        echo ""
        echo "🔧 Troubleshooting:"
        echo "   • Check the detailed output above for specific failures"
        echo "   • For Phase 1: Fix contract mismatches or missing env vars"
        echo "   • For Phase 2: Check Docker services and auth endpoint"
        echo "   • For Phase 3: Verify CORS configuration and proxy routing"
        echo "   • For Phase 4: Review regression diff and update baseline if needed"
        exit 1
    fi
}

# Run main function
main "$@"