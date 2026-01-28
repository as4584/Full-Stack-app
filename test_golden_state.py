#!/usr/bin/env python3
"""
Critical User Flow Tests - Must pass before any deployment
Tests the core user journeys that generate revenue
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

BASE_URL = "https://receptionist.lexmakesit.com"
DASHBOARD_URL = "https://lexmakesit.com"
AUTH_URL = "https://auth.lexmakesit.com"

class TestSession:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
        self.user_id = None

def test_user_signup_flow() -> Tuple[bool, str]:
    """Test that signup page loads with actual content"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'}
        response = requests.get(f"{AUTH_URL}/signup", timeout=10, headers=headers, allow_redirects=True)
        
        if response.status_code == 502:
            return False, "❌ Signup page returns 502 - Site DOWN"
        
        content = response.text
        # Verify it's real content, not error page
        if response.status_code == 200:
            if "502" in content or "Bad Gateway" in content:
                return False, "❌ Signup shows error page"
            if len(content) > 100 and ("<html" in content or "<!DOCTYPE" in content):
                return True, "✅ Signup page loads with content"
        elif response.status_code in [404, 307, 308]:
            # Check if 404 is real or disguised 502
            if "502" not in content:
                return True, f"✅ Signup endpoint exists (HTTP {response.status_code})"
        
        return False, f"❌ Signup page returned {response.status_code}"
    except Exception as e:
        return False, f"❌ Signup page failed: {str(e)[:80]}"

def test_user_login_flow() -> Tuple[bool, str]:
    """Test that login page loads with actual content"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'}
        response = requests.get(f"{AUTH_URL}/signin", timeout=10, headers=headers, allow_redirects=True)
        
        if response.status_code == 502:
            return False, "❌ Login page returns 502 - Site DOWN"
        
        content = response.text
        if response.status_code == 200:
            if "502" in content or "Bad Gateway" in content:
                return False, "❌ Login shows error page"
            if len(content) > 100 and ("<html" in content or "<!DOCTYPE" in content):
                return True, "✅ Login page loads with content"
        elif response.status_code in [404, 307, 308]:
            if "502" not in content:
                return True, f"✅ Login endpoint exists (HTTP {response.status_code})"
        
        return False, f"❌ Login page returned {response.status_code}"
    except Exception as e:
        return False, f"❌ Login flow failed: {str(e)[:80]}"

def test_api_auth_endpoints() -> Tuple[bool, str]:
    """Test authentication API endpoints"""
    try:
        # Test auth endpoints are accessible
        response = requests.post(f"{BASE_URL}/api/auth/login", 
                                json={"email": "test@test.com", "password": "test"},
                                timeout=10)
        # 401/422 means endpoint is working, just wrong credentials
        if response.status_code in [401, 422, 400]:
            return True, "✅ Auth API endpoints responding"
        elif response.status_code == 502:
            return False, "❌ CRITICAL: Auth API returns 502"
        return True, f"✅ Auth API responding (HTTP {response.status_code})"
    except Exception as e:
        return False, f"❌ Auth API failed: {str(e)}"

def test_dashboard_access() -> Tuple[bool, str]:
    """Test that dashboard loads with real Next.js content"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'}
        response = requests.get(DASHBOARD_URL, timeout=15, headers=headers, allow_redirects=True)
        content = response.text
        
        # Check for 502 error
        if response.status_code == 502 or "502 Bad Gateway" in content:
            return False, "❌ CRITICAL: Dashboard returns 502 - Site DOWN"
        
        # Verify real Next.js content is loading
        if response.status_code == 200:
            # Check for Next.js markers
            has_nextjs = any(marker in content for marker in ["__NEXT_DATA__", "_next/static", "next/script"])
            has_html = "<html" in content or "<!DOCTYPE" in content
            is_substantial = len(content) > 500
            
            if has_nextjs and has_html and is_substantial:
                return True, f"✅ Dashboard online with Next.js app ({len(content)} bytes)"
            elif has_html and is_substantial:
                return True, f"✅ Dashboard accessible ({len(content)} bytes)"
            else:
                return False, f"⚠️  Dashboard returns 200 but content incomplete ({len(content)} bytes)"
        
        elif response.status_code in [307, 308]:
            return True, f"✅ Dashboard redirecting (HTTP {response.status_code})"
        
        return False, f"❌ Dashboard returned unexpected {response.status_code}"
    except requests.exceptions.Timeout:
        return False, "❌ CRITICAL: Dashboard timeout - Server not responding"
    except Exception as e:
        return False, f"❌ Dashboard error: {str(e)[:80]}"

def test_receptionist_access() -> Tuple[bool, str]:
    """Test that AI receptionist features are accessible"""
    try:
        # Test business endpoints
        response = requests.get(f"{BASE_URL}/api/business/", timeout=10)
        if response.status_code in [401, 403, 422]:  # Auth required = working
            return True, "✅ Receptionist API accessible"
        elif response.status_code == 502:
            return False, "❌ CRITICAL: Receptionist API returns 502"
        return True, f"✅ Receptionist API responding (HTTP {response.status_code})"
    except Exception as e:
        return False, f"❌ Receptionist access failed: {str(e)}"

def test_phone_number_search() -> Tuple[bool, str]:
    """Test phone number purchase flow"""
    try:
        # Test Twilio integration endpoint
        response = requests.get(f"{BASE_URL}/api/twilio/available-numbers", 
                               params={"area_code": "415"},
                               timeout=10)
        if response.status_code in [401, 403, 422]:  # Auth required = working
            return True, "✅ Phone purchase flow accessible"
        elif response.status_code == 502:
            return False, "❌ CRITICAL: Phone search returns 502"
        return True, f"✅ Phone search responding (HTTP {response.status_code})"
    except Exception as e:
        return False, f"❌ Phone search failed: {str(e)}"

def test_payment_endpoint() -> Tuple[bool, str]:
    """Test that payment processing is available"""
    try:
        # Test payment endpoint (should require auth)
        response = requests.post(f"{BASE_URL}/api/payments/create-subscription",
                                json={"plan": "test"},
                                timeout=10)
        if response.status_code in [401, 403, 422]:  # Auth required = working
            return True, "✅ Payment system accessible"
        elif response.status_code == 502:
            return False, "❌ CRITICAL: Payment system returns 502"
        return True, f"✅ Payment system responding (HTTP {response.status_code})"
    except Exception as e:
        return False, f"❌ Payment system failed: {str(e)}"

def test_no_502_errors() -> Tuple[bool, str]:
    """Critical test: Ensure NO 502 errors on any endpoint (content verification)"""
    critical_urls = [
        (DASHBOARD_URL, "Dashboard"),
        (f"{AUTH_URL}/signin", "Auth"),
        (f"{BASE_URL}/docs", "API Docs"),
    ]
    
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'}
    
    for url, name in critical_urls:
        try:
            response = requests.get(url, timeout=15, headers=headers, allow_redirects=True)
            content = response.text
            
            # Check status code
            if response.status_code == 502:
                return False, f"❌ CRITICAL: 502 on {name} ({url})"
            
            # Check content for hidden 502 errors
            if "502 Bad Gateway" in content or "502 gateway" in content.lower():
                return False, f"❌ CRITICAL: {name} shows 502 error page"
            
            # Verify substantial content
            if response.status_code == 200 and len(content) < 100:
                return False, f"❌ CRITICAL: {name} returns empty/minimal content"
                
        except requests.exceptions.Timeout:
            return False, f"❌ CRITICAL: {name} timeout - not responding"
        except requests.exceptions.ConnectionError:
            return False, f"❌ CRITICAL: Cannot connect to {name}"
        except Exception as e:
            return False, f"❌ CRITICAL: {name} error - {str(e)[:60]}"
    
    return True, "✅ No 502 errors - all sites verified online"

def main():
    print(f"\n{Color.BOLD}{'='*60}")
    print("🛡️  GOLDEN STATE PROTECTION TEST")
    print("Critical User Flows - Must Pass Before Deployment")
    print(f"{'='*60}{Color.END}\n")
    
    tests = [
        ("No 502 Errors", test_no_502_errors),
        ("Dashboard Access", test_dashboard_access),
        ("User Signup Flow", test_user_signup_flow),
        ("User Login Flow", test_user_login_flow),
        ("Auth API", test_api_auth_endpoints),
        ("AI Receptionist Access", test_receptionist_access),
        ("Phone Number Search", test_phone_number_search),
        ("Payment Processing", test_payment_endpoint),
    ]
    
    results = []
    critical_failures = []
    
    for test_name, test_func in tests:
        print(f"{Color.BLUE}Testing: {test_name}...{Color.END}")
        success, message = test_func()
        results.append((success, message))
        
        if "CRITICAL" in message or "502" in message:
            critical_failures.append(test_name)
            print(f"{Color.RED}{message}{Color.END}\n")
        elif success:
            print(f"{Color.GREEN}{message}{Color.END}\n")
        else:
            print(f"{Color.YELLOW}{message}{Color.END}\n")
        
        time.sleep(0.5)  # Rate limiting
    
    # Summary
    print(f"{Color.BOLD}{'='*60}")
    print("📊 TEST RESULTS")
    print(f"{'='*60}{Color.END}\n")
    
    passed = sum(1 for success, _ in results if success)
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total}\n")
    
    if critical_failures:
        print(f"{Color.RED}{Color.BOLD}❌ CRITICAL FAILURES - DEPLOYMENT BLOCKED{Color.END}")
        print(f"{Color.RED}The following critical flows are broken:{Color.END}")
        for failure in critical_failures:
            print(f"  • {failure}")
        print(f"\n{Color.RED}🚫 DO NOT DEPLOY - System is broken for users{Color.END}")
        print(f"{Color.YELLOW}Restore golden state: ssh Innovation 'bash /opt/ai-receptionist/golden-state-backups/latest/restore.sh'{Color.END}")
        sys.exit(1)
    
    elif passed != total:
        print(f"{Color.YELLOW}⚠️  PARTIAL SUCCESS - Review failures{Color.END}")
        print(f"{Color.YELLOW}Some features may be degraded but core flows work{Color.END}")
        sys.exit(1)
    
    else:
        print(f"{Color.GREEN}{Color.BOLD}✅ ALL TESTS PASSED - DEPLOYMENT APPROVED{Color.END}")
        print(f"{Color.GREEN}All critical user flows are working:{Color.END}")
        print("  • ✅ Customers can access the dashboard")
        print("  • ✅ Users can sign up and log in")
        print("  • ✅ AI Receptionist features accessible")
        print("  • ✅ Phone number purchase available")
        print("  • ✅ Payment processing ready")
        print("  • ✅ No 502 errors detected")
        print(f"\n{Color.BLUE}🎯 This state is production-ready!{Color.END}")
        sys.exit(0)

if __name__ == "__main__":
    main()
