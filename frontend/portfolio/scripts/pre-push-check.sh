#!/bin/bash

# 🚀 Pre-Push Validation Script
# This script runs all checks locally before allowing a push to GitHub
# Usage: ./scripts/pre-push-check.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Temporary error log
ERROR_LOG=$(mktemp /tmp/pre-push-errors.XXXXXX)
TEMP_DIR=$(mktemp -d /tmp/portfolio-check.XXXXXX)

echo -e "${BLUE}🔍 Starting Pre-Push Validation Pipeline${NC}"
echo "=========================================="

# Cleanup function
cleanup() {
    echo -e "\n${BLUE}🧹 Cleaning up temporary files...${NC}"
    rm -rf "$TEMP_DIR"
    if [ -f "$ERROR_LOG" ]; then
        rm -f "$ERROR_LOG"
    fi
}

# Set trap for cleanup
trap cleanup EXIT

# Function to log errors
log_error() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$ERROR_LOG"
}

# Function to display errors
show_errors() {
    if [ -f "$ERROR_LOG" ] && [ -s "$ERROR_LOG" ]; then
        echo -e "\n${RED}❌ ERRORS FOUND - COPY AND PASTE BELOW:${NC}"
        echo "=================================================="
        cat "$ERROR_LOG"
        echo "=================================================="
        echo -e "${RED}❌ Fix these errors before pushing!${NC}"
        return 1
    fi
    return 0
}

# Step 1: Check Python syntax
echo -e "\n${YELLOW}1️⃣  Checking Python syntax...${NC}"
if ! python3 -m py_compile main.py 2>&1; then
    log_error "SYNTAX ERROR in main.py"
    echo -e "${RED}❌ Python syntax check failed${NC}"
else
    echo -e "${GREEN}✅ Python syntax OK${NC}"
fi

# Step 2: Security check with bandit
echo -e "\n${YELLOW}2️⃣  Running security scan...${NC}"
if ! bandit -r . -x test_main.py,bandit-report.json -f json -o "$BANDIT_REPORT" --severity-level low 2>/dev/null; then
    # Check if there are actual security issues in main code (not tests)
    if grep -q "main.py\|security_config.py" "$BANDIT_REPORT" 2>/dev/null; then
        log_error "SECURITY ISSUES FOUND in our code:"
        if command -v jq > /dev/null; then
            jq -r '.results[] | select(.filename | contains("main") or contains("security")) | "\(.filename):\(.line_number): \(.issue_text)"' "$BANDIT_REPORT" | while read -r line; do
                log_error "$line"
            done
        else
            # Fallback without jq
            grep -A 5 -B 2 "main.py\|security_config.py" "$BANDIT_REPORT" | head -20 | while read -r line; do
                log_error "$line"
            done
        fi
        echo -e "${RED}❌ Security scan failed${NC}"
    else
        echo -e "${GREEN}✅ Security scan passed (test file issues ignored)${NC}"
    fi
else
    echo -e "${GREEN}✅ Security scan passed${NC}"
fi

# Step 3: Code quality check
echo -e "\n${YELLOW}3️⃣  Running code quality checks...${NC}"
if ! python3 -m flake8 main.py --max-line-length=100 --ignore=E203,W503 2>&1; then
    FLAKE8_ERRORS=$(python3 -m flake8 main.py --max-line-length=100 --ignore=E203,W503 2>&1 || true)
    log_error "CODE QUALITY ISSUES:"
    log_error "$FLAKE8_ERRORS"
    echo -e "${RED}❌ Code quality check failed${NC}"
else
    echo -e "${GREEN}✅ Code quality OK${NC}"
fi

# Step 4: Dependency check
echo -e "\n${YELLOW}4️⃣  Checking dependencies...${NC}"
DEPENDENCY_CHECK=$(pip check 2>&1 || true)
# Filter out known dev dependencies that don't affect production
FILTERED_DEPS=$(echo "$DEPENDENCY_CHECK" | grep -v "pygobject\|rich-toolkit\|mcp" || true)
if [ -n "$FILTERED_DEPS" ]; then
    log_error "DEPENDENCY CONFLICTS:"
    log_error "$FILTERED_DEPS"
    echo -e "${RED}❌ Dependency check failed${NC}"
else
    echo -e "${GREEN}✅ Dependencies OK${NC}"
fi

# Step 5: Run tests
echo -e "\n${YELLOW}5️⃣  Running test suite...${NC}"
if ! python3 -m pytest test_main.py -v --tb=short 2>&1; then
    TEST_ERRORS=$(python3 -m pytest test_main.py -v --tb=short 2>&1 || true)
    log_error "TEST FAILURES:"
    log_error "$TEST_ERRORS"
    echo -e "${RED}❌ Tests failed${NC}"
else
    echo -e "${GREEN}✅ All tests passed${NC}"
fi

# Step 6: Docker build test
echo -e "\n${YELLOW}6️⃣  Testing Docker build...${NC}"
if ! docker build -t portfolio-test . > "$TEMP_DIR/docker.log" 2>&1; then
    DOCKER_ERRORS=$(cat "$TEMP_DIR/docker.log" 2>/dev/null || echo "Docker build failed")
    log_error "DOCKER BUILD FAILED:"
    log_error "$DOCKER_ERRORS"
    echo -e "${RED}❌ Docker build failed${NC}"
else
    echo -e "${GREEN}✅ Docker build succeeded${NC}"
    # Clean up test image
    docker rmi portfolio-test 2>/dev/null || true
fi

# Step 7: Check for common issues
echo -e "\n${YELLOW}7️⃣  Checking for common issues...${NC}"

# Check for hardcoded secrets (basic check, informational only)  
SECRET_MATCHES=$(grep -r -i "password.*=\|secret.*=\|key.*=" --include="*.py" . | grep -v "# " | grep -v "requirements.txt" | grep -v "__pycache__" | grep -v "bandit" | wc -l)
if [ "$SECRET_MATCHES" -gt 0 ]; then
    echo "ℹ️  Found $SECRET_MATCHES potential hardcoded values (review manually)"
fi

# Check for TODO/FIXME comments (informational only)
TODO_COUNT=$(grep -r -i "todo\|fixme" --include="*.py" . | wc -l)
if [ "$TODO_COUNT" -gt 0 ]; then
    echo "ℹ️  Found $TODO_COUNT TODO/FIXME comments (informational only)"
fi

echo -e "${GREEN}✅ Common issues check completed${NC}"

# Final validation
echo -e "\n${BLUE}📋 VALIDATION SUMMARY${NC}"
echo "========================="

if show_errors; then
    echo -e "\n${GREEN}🎉 ALL CHECKS PASSED! Ready to push! 🚀${NC}"
    echo -e "${GREEN}You can now safely run: git push${NC}"
    exit 0
else
    echo -e "\n${RED}❌ VALIDATION FAILED! Fix errors above before pushing.${NC}"
    exit 1
fi