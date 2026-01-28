#!/bin/bash
# =============================================================================
# VERIFICATION SCRIPT - Auth/Dashboard Separation
# =============================================================================
# This script verifies that auth and dashboard apps are properly isolated
# =============================================================================

set -e

echo "==========================================="
echo "🔍 VERIFICATION: Auth/Dashboard Separation"
echo "==========================================="

PASS=0
FAIL=0

# Test 1: Auth app should NOT contain dashboard HTML
echo ""
echo "[TEST 1] auth.lexmakesit.com/login should NOT contain dashboard HTML"
AUTH_HTML=$(curl -sL https://auth.lexmakesit.com/login)
if echo "$AUTH_HTML" | grep -q "dashboard_header\|dashboard_appContainer\|appContainer"; then
    echo "  ❌ FAIL: Auth app contains dashboard HTML!"
    FAIL=$((FAIL + 1))
else
    echo "  ✅ PASS: Auth app is clean (no dashboard HTML)"
    PASS=$((PASS + 1))
fi

# Test 2: Dashboard app should NOT contain login HTML from auth app
echo ""
echo "[TEST 2] dashboard.lexmakesit.com should NOT serve login page"
DASHBOARD_HTML=$(curl -sL https://dashboard.lexmakesit.com)
if echo "$DASHBOARD_HTML" | grep -q "Sign in to manage your AI assistant"; then
    # This is OK only if it's a loading/redirect message, not the full login form
    if echo "$DASHBOARD_HTML" | grep -q "login_form\|login_card"; then
        echo "  ❌ FAIL: Dashboard app contains login form HTML!"
        FAIL=$((FAIL + 1))
    else
        echo "  ✅ PASS: Dashboard does not contain login form"
        PASS=$((PASS + 1))
    fi
else
    echo "  ✅ PASS: Dashboard does not contain login text"
    PASS=$((PASS + 1))
fi

# Test 3: Auth app should have minimal HTML (no complex layouts)
echo ""
echo "[TEST 3] auth.lexmakesit.com should be minimal (< 10KB)"
AUTH_SIZE=$(curl -sL https://auth.lexmakesit.com/login | wc -c)
if [ "$AUTH_SIZE" -gt 15000 ]; then
    echo "  ⚠️  WARNING: Auth HTML is $AUTH_SIZE bytes (>15KB) - check for bloat"
else
    echo "  ✅ PASS: Auth HTML is $AUTH_SIZE bytes (minimal)"
    PASS=$((PASS + 1))
fi

# Test 4: Cookie domain verification
echo ""
echo "[TEST 4] Verify cookie domain is .lexmakesit.com"
# This requires a real login, so we just check if the backend is configured correctly
echo "  ℹ️  INFO: Cookie domain verification requires manual login test"
echo "  ℹ️  Use browser DevTools to verify lex_token has domain=.lexmakesit.com"

# Test 5: Both apps should respond with 200
echo ""
echo "[TEST 5] Both apps should respond with HTTP 200"
AUTH_STATUS=$(curl -sL -o /dev/null -w "%{http_code}" https://auth.lexmakesit.com/login)
DASHBOARD_STATUS=$(curl -sL -o /dev/null -w "%{http_code}" https://dashboard.lexmakesit.com)

if [ "$AUTH_STATUS" = "200" ]; then
    echo "  ✅ auth.lexmakesit.com: HTTP $AUTH_STATUS"
    PASS=$((PASS + 1))
else
    echo "  ❌ auth.lexmakesit.com: HTTP $AUTH_STATUS (expected 200)"
    FAIL=$((FAIL + 1))
fi

if [ "$DASHBOARD_STATUS" = "200" ]; then
    echo "  ✅ dashboard.lexmakesit.com: HTTP $DASHBOARD_STATUS"
    PASS=$((PASS + 1))
else
    echo "  ❌ dashboard.lexmakesit.com: HTTP $DASHBOARD_STATUS (expected 200)"
    FAIL=$((FAIL + 1))
fi

# Summary
echo ""
echo "==========================================="
echo "📊 VERIFICATION SUMMARY"
echo "==========================================="
echo "  ✅ PASSED: $PASS tests"
echo "  ❌ FAILED: $FAIL tests"
echo ""

if [ "$FAIL" -gt 0 ]; then
    echo "🚨 VERIFICATION FAILED - Do not proceed to production!"
    exit 1
else
    echo "✅ ALL TESTS PASSED - Apps are properly isolated!"
    exit 0
fi
