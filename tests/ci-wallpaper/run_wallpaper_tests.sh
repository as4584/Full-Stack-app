#!/bin/bash

# CI Wallpaper Asset Reliability System
# Ensures wallpaper.gif assets never break in production

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Logging functions
log_header() {
    echo -e "${BLUE}\n=== $1 ===${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

show_usage() {
    echo "Usage: $0 [phase1|phase2|phase3|phase4|all] [options]"
    echo ""
    echo "PHASES:"
    echo "  phase1    - Asset Availability Check (HTTP validation)"
    echo "  phase2    - Rendering Validation (Browser tests)"
    echo "  phase3    - Cache Safety (CDN & cache headers)"
    echo "  phase4    - Visual Regression (Screenshot comparison)"
    echo "  all       - Run all phases sequentially"
    echo ""
    echo "OPTIONS:"
    echo "  --create-baseline    Create new visual baseline (phase4 only)"
    echo "  --verbose           Show detailed output"
    echo "  --continue-on-error Continue even if a phase fails"
    echo "  --help              Show this help"
    echo ""
    echo "EXAMPLES:"
    echo "  $0 all                    # Run all phases"
    echo "  $0 phase1                 # Check asset availability only"
    echo "  $0 phase4 --create-baseline  # Create visual baseline"
}

# Default options
PHASE="all"
CREATE_BASELINE=false
VERBOSE=false
CONTINUE_ON_ERROR=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        phase1|phase2|phase3|phase4|all)
            PHASE="$1"
            shift
            ;;
        --create-baseline)
            CREATE_BASELINE=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --continue-on-error)
            CONTINUE_ON_ERROR=true
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

log_header "WALLPAPER ASSET RELIABILITY CI SYSTEM"
log_info "Project Root: $PROJECT_ROOT"
log_info "Test Directory: $TEST_DIR"
log_info "Running Phase: $PHASE"

# Ensure Python environment is set up
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 is required but not installed"
    exit 1
fi

# Install Python dependencies if needed
REQUIREMENTS_FILE="$TEST_DIR/requirements.txt"
if [ -f "$REQUIREMENTS_FILE" ]; then
    log_info "Installing Python dependencies..."
    python3 -m pip install -r "$REQUIREMENTS_FILE" --quiet
fi

# Install Playwright browsers if needed (for phases 2 and 4)
if [ "$PHASE" = "phase2" ] || [ "$PHASE" = "phase4" ] || [ "$PHASE" = "all" ]; then
    if ! python3 -c "import playwright" 2>/dev/null; then
        log_info "Installing Playwright..."
        python3 -m pip install playwright --quiet
    fi
    
    # Install browser binaries
    if [ ! -d "$HOME/.cache/ms-playwright" ] || [ -z "$(ls -A $HOME/.cache/ms-playwright 2>/dev/null)" ]; then
        log_info "Installing Playwright browsers..."
        python3 -m playwright install chromium --quiet
    fi
fi

# Phase execution function
run_phase() {
    local phase_name=$1
    local script_name=$2
    local description=$3
    local extra_args=$4
    
    log_header "$phase_name: $description"
    
    local script_path="$TEST_DIR/$script_name"
    
    if [ ! -f "$script_path" ]; then
        log_error "Phase script not found: $script_path"
        return 1
    fi
    
    # Make script executable
    chmod +x "$script_path"
    
    # Run the phase
    local start_time=$(date +%s)
    
    if [ "$VERBOSE" = true ]; then
        python3 "$script_path" "$PROJECT_ROOT" $extra_args
    else
        python3 "$script_path" "$PROJECT_ROOT" $extra_args 2>&1
    fi
    
    local exit_code=$?
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    if [ $exit_code -eq 0 ]; then
        log_success "$phase_name completed successfully (${duration}s)"
        return 0
    else
        log_error "$phase_name failed (exit code: $exit_code, duration: ${duration}s)"
        return 1
    fi
}

# Track overall results
OVERALL_SUCCESS=true
PHASES_RUN=()
PHASES_PASSED=()
PHASES_FAILED=()

# Execute phases
if [ "$PHASE" = "all" ] || [ "$PHASE" = "phase1" ]; then
    PHASES_RUN+=("Phase 1")
    if run_phase "PHASE 1" "phase1_asset_availability.py" "Asset Availability Check"; then
        PHASES_PASSED+=("Phase 1")
    else
        PHASES_FAILED+=("Phase 1")
        OVERALL_SUCCESS=false
        if [ "$CONTINUE_ON_ERROR" = false ] && [ "$PHASE" = "all" ]; then
            log_error "Phase 1 failed, stopping execution"
            exit 1
        fi
    fi
fi

if [ "$PHASE" = "all" ] || [ "$PHASE" = "phase2" ]; then
    PHASES_RUN+=("Phase 2")
    if run_phase "PHASE 2" "phase2_rendering_validation.py" "Rendering Validation"; then
        PHASES_PASSED+=("Phase 2")
    else
        PHASES_FAILED+=("Phase 2")
        OVERALL_SUCCESS=false
        if [ "$CONTINUE_ON_ERROR" = false ] && [ "$PHASE" = "all" ]; then
            log_error "Phase 2 failed, stopping execution"
            exit 1
        fi
    fi
fi

if [ "$PHASE" = "all" ] || [ "$PHASE" = "phase3" ]; then
    PHASES_RUN+=("Phase 3")
    if run_phase "PHASE 3" "phase3_cache_safety.py" "Cache Safety Check"; then
        PHASES_PASSED+=("Phase 3")
    else
        PHASES_FAILED+=("Phase 3")
        OVERALL_SUCCESS=false
        if [ "$CONTINUE_ON_ERROR" = false ] && [ "$PHASE" = "all" ]; then
            log_error "Phase 3 failed, stopping execution"
            exit 1
        fi
    fi
fi

if [ "$PHASE" = "all" ] || [ "$PHASE" = "phase4" ]; then
    PHASES_RUN+=("Phase 4")
    local extra_args=""
    if [ "$CREATE_BASELINE" = true ]; then
        extra_args="--create-baseline"
    fi
    
    if run_phase "PHASE 4" "phase4_visual_regression.py" "Visual Regression Protection" "$extra_args"; then
        PHASES_PASSED+=("Phase 4")
    else
        PHASES_FAILED+=("Phase 4")
        OVERALL_SUCCESS=false
    fi
fi

# Final summary
log_header "WALLPAPER CI SYSTEM SUMMARY"

log_info "Phases run: ${#PHASES_RUN[@]}"
log_success "Phases passed: ${#PHASES_PASSED[@]} (${PHASES_PASSED[*]})"

if [ ${#PHASES_FAILED[@]} -gt 0 ]; then
    log_error "Phases failed: ${#PHASES_FAILED[@]} (${PHASES_FAILED[*]})"
fi

echo ""
if [ "$OVERALL_SUCCESS" = true ]; then
    log_success "🎉 ALL WALLPAPER TESTS PASSED - Assets are safe for deployment!"
    echo -e "${GREEN}"
    echo "  ✅ Wallpaper assets are accessible and valid"
    echo "  ✅ Wallpapers render correctly on all target pages"
    echo "  ✅ Cache configuration is optimized and safe"
    echo "  ✅ No visual regressions detected"
    echo -e "${NC}"
    exit 0
else
    log_error "🚨 WALLPAPER TESTS FAILED - DO NOT DEPLOY"
    echo -e "${RED}"
    echo "  ❌ Wallpaper assets may be broken or missing"
    echo "  ❌ Users may see broken backgrounds or empty pages"
    echo "  ❌ Brand consistency is at risk"
    echo ""
    echo "  📋 Action Required:"
    echo "     1. Check individual phase outputs above"
    echo "     2. Fix wallpaper asset issues"
    echo "     3. Re-run tests before deploying"
    echo -e "${NC}"
    exit 1
fi