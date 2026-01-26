#!/bin/bash
set -e

echo "=== PRODUCTION SMOKE TEST: dashboard.lexmakesit.com ==="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PRODUCTION_URL="https://dashboard.lexmakesit.com"
FAILED=0

# Test 1: DNS Resolution
echo -e "${YELLOW}[1/6] Testing DNS resolution...${NC}"
DNS_IP=$(dig +short dashboard.lexmakesit.com | head -1)
if [ -n "$DNS_IP" ]; then
    echo -e "${GREEN}✓ DNS resolves to: $DNS_IP${NC}"
else
    echo -e "${RED}✗ DNS resolution failed${NC}"
    FAILED=1
fi

# Test 2: HTTPS Connectivity
echo ""
echo -e "${YELLOW}[2/6] Testing HTTPS connectivity...${NC}"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$PRODUCTION_URL")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "307" ] || [ "$HTTP_CODE" = "302" ]; then
    echo -e "${GREEN}✓ HTTPS returns HTTP $HTTP_CODE${NC}"
else
    echo -e "${RED}✗ HTTPS failed with HTTP $HTTP_CODE (expected 200/307/302)${NC}"
    FAILED=1
fi

# Test 3: HTML Content (not JSON, not error)
echo ""
echo -e "${YELLOW}[3/6] Testing response content type...${NC}"
# Follow redirects to get final page
RESPONSE_BODY=$(curl -sL --max-time 10 "$PRODUCTION_URL")

# Check if response contains HTML tags (Next.js may not have DOCTYPE in streaming)
if echo "$RESPONSE_BODY" | grep -qi "<meta.*charset\|<div\|<html"; then
    echo -e "${GREEN}✓ Response is HTML${NC}"
else
    echo -e "${RED}✗ Response is not HTML${NC}"
    echo "First 200 chars:"
    echo "$RESPONSE_BODY" | head -c 200
    FAILED=1
fi

# Test 4: No Next.js Error Overlay or Dev Warnings
echo ""
echo -e "${YELLOW}[4/6] Checking for Next.js dev warnings...${NC}"
# Look for actual ERROR strings, not normal Next.js production artifacts
if echo "$RESPONSE_BODY" | grep -Ei "next.*dev.*error|__nextjs.*error|missing required html tags|hydration.*failed|react.*development.*warning"; then
    echo -e "${RED}✗ Found Next.js dev warning/error strings in response${NC}"
    echo "Matches:"
    echo "$RESPONSE_BODY" | grep -Ei "next.*dev.*error|__nextjs.*error|missing required html tags|hydration.*failed" | head -5
    FAILED=1
else
    echo -e "${GREEN}✓ No Next.js error overlay detected${NC}"
fi

# Test 5: Dashboard Shell Renders
echo ""
echo -e "${YELLOW}[5/6] Checking dashboard shell...${NC}"
# Look for common dashboard elements (adjust based on your actual HTML)
if echo "$RESPONSE_BODY" | grep -qi "dashboard\|app\|_next"; then
    echo -e "${GREEN}✓ Dashboard shell appears to render${NC}"
else
    echo -e "${RED}✗ Dashboard shell not detected${NC}"
    FAILED=1
fi

# Test 6: Port 3000 NOT publicly accessible
echo ""
echo -e "${YELLOW}[6/6] Verifying port 3000 is locked down...${NC}"
if timeout 3 bash -c "nc -zv $DNS_IP 3000 2>&1" | grep -q "succeeded"; then
    echo -e "${RED}✗ CRITICAL: Port 3000 is publicly accessible!${NC}"
    echo "Action required: ssh droplet 'sudo ufw deny 3000'"
    FAILED=1
else
    echo -e "${GREEN}✓ Port 3000 is not publicly accessible${NC}"
fi

# Final Report
echo ""
echo "========================================="
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ ALL TESTS PASSED${NC}"
    echo "========================================="
    echo ""
    echo "Production is healthy:"
    echo "  URL: $PRODUCTION_URL"
    echo "  Status: ✓ Operational"
    echo "  No dev warnings: ✓"
    echo "  Port security: ✓"
    echo ""
    exit 0
else
    echo -e "${RED}✗ SMOKE TEST FAILED${NC}"
    echo "========================================="
    echo ""
    echo "Issues detected. Review logs above."
    echo "DO NOT deploy to production."
    echo ""
    exit 1
fi
