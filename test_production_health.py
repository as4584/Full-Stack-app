#!/usr/bin/env python3
"""
Production Health Test - Fails if any 502 errors detected
Tests all production URLs and ensures they're actually working
"""
import requests
import sys
import time
from typing import Dict, List, Tuple

class Color:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def test_url(url: str, expected_codes: List[int], description: str) -> Tuple[bool, int, str]:
    """
    Test a URL and return (success, status_code, message)
    """
    try:
        response = requests.get(url, timeout=10, allow_redirects=False)
        status_code = response.status_code
        
        # 502 is ALWAYS a failure
        if status_code == 502:
            return False, status_code, f"❌ CRITICAL: 502 Bad Gateway detected!"
        
        # Check if status code is expected
        if status_code in expected_codes:
            return True, status_code, f"✅ {description}: HTTP {status_code}"
        else:
            return False, status_code, f"⚠️  {description}: Unexpected HTTP {status_code} (expected {expected_codes})"
            
    except requests.exceptions.Timeout:
        return False, 0, f"❌ {description}: Request timeout (>10s)"
    except requests.exceptions.ConnectionError as e:
        return False, 0, f"❌ {description}: Connection failed - {str(e)}"
    except Exception as e:
        return False, 0, f"❌ {description}: Error - {str(e)}"

def check_container_running(container_name: str) -> Tuple[bool, str]:
    """Check if a Docker container is running on the server"""
    import subprocess
    try:
        result = subprocess.run(
            ["ssh", "Innovation", f"docker ps --filter name={container_name} --format '{{{{.Status}}}}'"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0 and "Up" in result.stdout:
            return True, f"✅ {container_name} is running"
        else:
            return False, f"❌ {container_name} is NOT running"
    except Exception as e:
        return False, f"❌ Could not check {container_name}: {str(e)}"

def main():
    print(f"\n{Color.BOLD}{'='*60}")
    print("🔍 PRODUCTION HEALTH TEST")
    print(f"{'='*60}{Color.END}\n")
    
    tests = [
        # (URL, expected_codes, description)
        ("https://lexmakesit.com/", [200, 307, 308], "Dashboard Homepage"),
        ("https://auth.lexmakesit.com/signin", [200, 404], "Auth Signin Page"),
        ("https://receptionist.lexmakesit.com/", [200, 405], "Backend API Root"),
        ("https://receptionist.lexmakesit.com/docs", [200], "API Documentation"),
    ]
    
    containers = [
        "dashboard_nextjs_prod",
        "auth_nextjs_prod",
        "ai-receptionist-app-1"
    ]
    
    results = []
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
            print(f"{Color.GREEN}{message}{Color.END}")
        else:
            all_passed = False
            print(f"{Color.RED}{message}{Color.END}")
    
    # Summary
    print(f"\n{Color.BOLD}{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}{Color.END}\n")
    
    passed = sum(1 for success, _ in results if success)
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total}")
    
    if critical_502_found:
        print(f"\n{Color.RED}{Color.BOLD}❌ CRITICAL FAILURE: 502 Bad Gateway Error Detected!{Color.END}")
        print(f"{Color.RED}The website is NOT accessible to users.{Color.END}")
        print(f"\n{Color.YELLOW}Next Steps:{Color.END}")
        print("1. SSH to server: ssh Innovation")
        print("2. Check container logs: docker logs dashboard_nextjs_prod")
        print("3. Restart Caddy: sudo systemctl restart caddy")
        print("4. Verify containers running: docker ps | grep -E 'dashboard|auth'")
        sys.exit(1)
    
    elif not all_passed:
        print(f"\n{Color.YELLOW}⚠️  PARTIAL FAILURE: Some tests failed{Color.END}")
        print(f"{Color.YELLOW}Check the failures above and fix them.{Color.END}")
        sys.exit(1)
    
    else:
        print(f"\n{Color.GREEN}{Color.BOLD}✅ ALL TESTS PASSED!{Color.END}")
        print(f"{Color.GREEN}All production services are healthy and responding correctly.{Color.END}")
        print(f"\n{Color.BLUE}Production URLs:{Color.END}")
        print("  • Dashboard: https://lexmakesit.com")
        print("  • Auth: https://auth.lexmakesit.com")
        print("  • API: https://receptionist.lexmakesit.com")
        sys.exit(0)

if __name__ == "__main__":
    main()
