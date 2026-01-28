#!/usr/bin/env python3
"""
Production Health Test - Fails if any 502 errors detected
Tests all production URLs and ensures they're actually working with real content
"""
import requests
import sys
import time
import re
from typing import Dict, List, Tuple

class Color:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def test_url_with_content(url: str, description: str, required_content: List[str] = None) -> Tuple[bool, int, str]:
    """
    Test a URL and verify actual content loads (not just status code)
    Returns (success, status_code, message)
    """
    try:
        # Test with actual browser headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
        
        response = requests.get(url, timeout=15, headers=headers, allow_redirects=True)
        status_code = response.status_code
        content = response.text
        
        # 502 is ALWAYS a critical failure
        if status_code == 502:
            return False, status_code, f"❌ CRITICAL: 502 Bad Gateway - Site is DOWN"
        
        # 503/504 are also critical failures
        if status_code in [503, 504]:
            return False, status_code, f"❌ CRITICAL: {status_code} - Service unavailable"
        
        # Check if we got actual HTML content (not error page)
        if status_code == 200:
            # Verify it's not an error page disguised as 200
            if "502 Bad Gateway" in content or "503 Service" in content:
                return False, 200, f"❌ {description}: Returns 200 but shows error page"
            
            # Check for actual HTML structure
            if not re.search(r'<html|<!DOCTYPE', content, re.IGNORECASE):
                return False, 200, f"❌ {description}: No HTML content returned"
            
            # Verify content length (not empty page)
            if len(content) < 100:
                return False, 200, f"❌ {description}: Response too short ({len(content)} bytes)"
            
            # Check for required content if specified
            if required_content:
                missing = [item for item in required_content if item not in content]
                if missing:
                    return False, 200, f"⚠️  {description}: Missing content: {missing[0]}"
            
            return True, status_code, f"✅ {description}: Online & serving content ({len(content)} bytes)"
        
        # 307/308 redirects are OK for Next.js
        elif status_code in [307, 308]:
            return True, status_code, f"✅ {description}: Redirecting (HTTP {status_code})"
        
        # 404 might be OK for some routes (but verify it's real 404, not 502 disguised)
        elif status_code == 404:
            if "502 Bad Gateway" in content:
                return False, 404, f"❌ {description}: 404 response contains 502 error"
            return True, status_code, f"✅ {description}: Route handling working (404)"
        
        # Unexpected status
        else:
            return False, status_code, f"⚠️  {description}: Unexpected HTTP {status_code}"
            
    except requests.exceptions.Timeout:
        return False, 0, f"❌ {description}: Timeout - Server not responding"
    except requests.exceptions.SSLError as e:
        return False, 0, f"❌ {description}: SSL Error - {str(e)[:100]}"
    except requests.exceptions.ConnectionError as e:
        error_msg = str(e)
        if "502" in error_msg:
            return False, 502, f"❌ CRITICAL: Connection returns 502 Bad Gateway"
        return False, 0, f"❌ {description}: Cannot connect - {error_msg[:100]}"
    except Exception as e:
        return False, 0, f"❌ {description}: Error - {str(e)[:100]}"

def check_container_healthy(container_name: str) -> Tuple[bool, str]:
    """Check if container is running AND responding to requests"""
    import subprocess
    
    # Map container to localhost port
    port_map = {
        "dashboard_nextjs_prod": 3000,
        "auth_nextjs_prod": 3001,
        "ai-receptionist-app-1": 8002
    }
    
    try:
        # Check if container is running
        result = subprocess.run(
            ["ssh", "Innovation", f"docker ps --filter name={container_name} --format '{{{{.Status}}}}'"],
            capture_output=True,
            text=True,
            timeout=10
        )70}")
    print("🔍 PRODUCTION HEALTH TEST - PRECISION MODE")
    print(f"{'='*70}{Color.END}\n")
    
    # Define tests with required content to verify real functionality
    url_tests = [
        ("https://lexmakesit.com/", "Dashboard Homepage", ["next", "script", "__NEXT_DATA__"]),
        ("https://auth.lexmakesit.com/signin", "Auth Signin", ["sign", "next"]),
        ("https://receptionist.lexmakesit.com/docs", "API Docs", ["swagger", "openapi", "FastAPI"]),
    ]
    
    containers = [
        "dashboard_nextjs_prod",
        "auth_nextjs_prod",
        "ai-receptionist-app-1"
    ]
    
    results = []
    critical_502_found = False
    critical_errors = []
    
    # Test URLs with content verification
    print(f"{Color.BLUE}━━━ Testing Production URLs (Content Verification) ━━━{Color.END}\n")
    for url, description, required_content in url_tests:
        success, status_code, message = test_url_with_content(url, description, required_content)
        results.append((success, message))
        
        if status_code == 502 or "502" in message:
            critical_502_found = True
            critical_errors.append(f"{description} returns 502")
            print(f"{Color.RED}{message}{Color.END}")
        elif "CRITICAL" in message:
            critical_502_found = True
            critical_errors.append(description)
            print(f"{Color.RED}{message}{Color.END}")
        elif success:
            print(f"{Color.GREEN}{message}{Color.END}")
        else:
            print(f"{Color.YELLOW}{message}{Color.END}")
    
    # Check container health (not just running, but responding)
    print(f"\n{Color.BLUE}━━━ Checking Container Health (Response Verification) ━━━{Color.END}\n")
    for container in containers:
        success, message = check_container_healthy(container)
        results.append((success, message))
        
        if "502" in message:
            critical_502_found = True
            critical_errors.append(f"{container} returns 502")
            print(f"{Color.RED}{message}{Color.END}")
        elif success:
            print(f"{Color.GREEN}{message}{Color.END}")
        else:
    all_passed = True
    critical_502_found = False
    
    # Test URLs
    print(f"{Color.BLUE}Testing Production URLs...{Color.END}\n")
    for url, expected_codes, description in tests:
        success, status_code, message = test_url(url, expected_codes, description)
        results.append((success, message))
        
        if status_code == 502:
            critical_502_found = True
            all_passed = False
            print(f"{Color.RED}{message}{Color.END}")
        elif success:
            print(f"{Color.GREEN}{message}{Color.END}")
        else:
            all_passed = False
            print(f"{Color.YELLOW}{message}{Color.END}")
    
    # Check containers
    print(f"\n{Color.BLUE}Checking Docker Containers...{Color.END}\n")
    for container in containers:
        success, message = check_container_running(container)
        results.append((success, message))
        
        if success:
      Verify Caddy is proxying correctly
    print(f"\n{Color.BLUE}━━━ Verifying Caddy Proxy Health ━━━{Color.END}\n")
    import subprocess
    try:
        caddy_status = subprocess.run(
            ["ssh", "Innovation", "sudo systemctl is-active caddy"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if "active" in caddy_status.stdout:
            print(f"{Color.GREEN}✅ Caddy is active and running{Color.END}")
            results.append((True, "Caddy active"))
        else:
            print(f"{Color.RED}❌ Caddy is NOT active{Color.END}")
            results.append((False, "Caddy not active"))
            critical_errors.append("Caddy not running")
    except Exception as e:
        print(f"{Color.YELLOW}⚠️  Could not check Caddy: {str(e)[:50]}{Color.END}")
    
    # Summary
    print(f"\n{Color.BOLD}{'='*70}")
    print("📊 PRECISION TEST RESULTS")
    print(f"{'='*70}{Color.END}\n")
    
    passed = sum(1 for success, _ in results if success)
    total = len(results)
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"Tests Passed: {passed}/{total} ({pass_rate:.1f}%)")
    
    if critical_502_found:
        print(f"\n{Color.RED}{Color.BOLD}🚨 CRITICAL FAILURE: 502 ERROR DETECTED{Color.END}")
        print(f"{Color.RED}{'━' * 70}{Color.END}")
        print(f"{Color.RED}Website is DOWN and NOT accessible to users.{Color.END}\n")
        
        print(f"{Color.BOLD}Failed Components:{Color.END}")
        for error in critical_errors:
            print(f"  ❌ {error}")
        
        print(f"\n{Color.YELLOW}{Color.BOLD}Resolution Steps:{Color.END}")
        print(f"{Color.YELLOW}1. Restart Caddy:{Color.END} ssh Innovation 'sudo systemctl restart caddy'")
        print(f"{Color.YELLOW}2. Check containers:{Color.END} ssh Innovation 'docker ps'")
        print(f"{Color.YELLOW}3. Check logs:{Color.END} ssh Innovation 'docker logs dashboard_nextjs_prod --tail 50'")
        print(f"{Color.YELLOW}4. Verify fix:{Color.END} python3 test_production_health.py")
        sys.exit(1)
    
    elif passed < total:
        print(f"\n{Color.YELLOW}⚠️  PARTIAL FAILURE: {total - passed} test(s) failed{Color.END}")
        print(f"{Color.YELLOW}Review failures above. Site may have degraded functionality.{Color.END}")
        sys.exit(1)
    
    else:
        print(f"\n{Color.GREEN}{Color.BOLD}✅ ALL PRECISION TESTS PASSED!{Color.END}")
        print(f"{Color.GREEN}{'━' * 70}{Color.END}")
        print(f"{Color.GREEN}Website is ONLINE and fully functional:{Color.END}\n")
        print(f"  ✅ Dashboard serving real content")
        print(f"  ✅ Auth pages loading correctly")
        print(f"  ✅ API documentation accessible")
        print(f"  ✅ All containers responding")
        print(f"  ✅ Caddy proxy working")
        print(f"  ✅ NO 502 errors detected")
        print(f"\n{Color.BLUE}🌐 Production URLs:{Color.END}")
        print("  • https://lexmakesit.com (Dashboard)")
        print("  • https://auth.lexmakesit.com (Authentication)")
        print("  • https://receptionist.lexmakesit.com (API)")
        print(f"\n{Color.GREEN}🎉 Site is ready for customers!{Color.END}ED!{Color.END}")
        print(f"{Color.GREEN}All production services are healthy and responding correctly.{Color.END}")
        print(f"\n{Color.BLUE}Production URLs:{Color.END}")
        print("  • Dashboard: https://lexmakesit.com")
        print("  • Auth: https://auth.lexmakesit.com")
        print("  • API: https://receptionist.lexmakesit.com")
        sys.exit(0)

if __name__ == "__main__":
    main()
