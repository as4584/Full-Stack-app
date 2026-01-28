#!/usr/bin/env python3
"""
E2E DASHBOARD RENDER TEST
This test MUST FAIL if the dashboard shows a white screen.
Used as a hard gate for deployments.

Exit codes:
    0 = Dashboard renders correctly
    1 = WHITE SCREEN or render failure detected
"""

import sys
import time
import subprocess
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from html.parser import HTMLParser

PRODUCTION_URL = "https://dashboard.lexmakesit.com"
TIMEOUT = 10

class HTMLContentParser(HTMLParser):
    """Parse HTML to detect if there's actual visible content"""
    def __init__(self):
        super().__init__()
        self.has_visible_content = False
        self.text_content = []
        self.in_script = False
        self.in_style = False
        
    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            if tag == 'script':
                self.in_script = True
            else:
                self.in_style = True
        # Check for visible elements
        if tag in ('div', 'h1', 'h2', 'h3', 'p', 'span', 'button', 'form', 'input', 'label'):
            self.has_visible_content = True
            
    def handle_endtag(self, tag):
        if tag == 'script':
            self.in_script = False
        elif tag == 'style':
            self.in_style = False
            
    def handle_data(self, data):
        # Collect text content (excluding scripts and styles)
        if not self.in_script and not self.in_style:
            stripped = data.strip()
            if stripped and len(stripped) > 3:
                self.text_content.append(stripped)


def test_dashboard_renders():
    """
    CRITICAL TEST: Verify dashboard renders visible UI
    
    Checks:
    1. HTTPS returns 200 or 307 (redirect is OK)
    2. Response is HTML (not JSON error)
    3. HTML contains visible DOM elements
    4. HTML contains actual text content
    5. Known UI elements present (login form, dashboard elements)
    """
    
    print("=" * 60)
    print("🧪 E2E DASHBOARD RENDER TEST")
    print("=" * 60)
    print()
    
    # Test 1: HTTP connectivity
    print("[1/5] Testing HTTPS connectivity...")
    try:
        req = Request(PRODUCTION_URL, headers={'User-Agent': 'E2E-Test/1.0'})
        response = urlopen(req, timeout=TIMEOUT)
        status_code = response.getcode()
        
        if status_code in (200, 307, 302):
            print(f"✅ PASS: HTTP {status_code}")
        else:
            print(f"❌ FAIL: Unexpected HTTP {status_code}")
            return False
            
    except (URLError, HTTPError) as e:
        print(f"❌ FAIL: Connection error: {e}")
        return False
    
    # Test 2: Follow redirects and get final content
    print("\n[2/5] Fetching final page content...")
    try:
        # Use curl to follow redirects
        result = subprocess.run(
            ['curl', '-sL', '--max-time', str(TIMEOUT), PRODUCTION_URL],
            capture_output=True,
            text=True,
            timeout=TIMEOUT + 2
        )
        
        if result.returncode != 0:
            print(f"❌ FAIL: curl failed with code {result.returncode}")
            return False
            
        html_content = result.stdout
        
        if not html_content or len(html_content) < 500:
            print(f"❌ FAIL: HTML too short ({len(html_content)} bytes). Likely white screen.")
            return False
            
        print(f"✅ PASS: Received {len(html_content)} bytes of HTML")
        
    except subprocess.TimeoutExpired:
        print("❌ FAIL: Request timed out")
        return False
    except Exception as e:
        print(f"❌ FAIL: Error fetching content: {e}")
        return False
    
    # Test 3: Parse HTML structure
    print("\n[3/5] Parsing HTML structure...")
    parser = HTMLContentParser()
    try:
        parser.feed(html_content)
    except Exception as e:
        print(f"❌ FAIL: HTML parsing error: {e}")
        return False
    
    if not parser.has_visible_content:
        print("❌ FAIL: No visible HTML elements detected (white screen)")
        return False
    
    print(f"✅ PASS: Found visible HTML elements")
    
    # Test 4: Check for actual text content
    print("\n[4/5] Checking for text content...")
    if len(parser.text_content) < 3:
        print(f"❌ FAIL: Insufficient text content ({len(parser.text_content)} text nodes)")
        print("This indicates a white screen or minimal render")
        return False
    
    # Join all text and check length
    all_text = ' '.join(parser.text_content)
    if len(all_text) < 100:
        print(f"❌ FAIL: Too little text content ({len(all_text)} chars)")
        return False
    
    print(f"✅ PASS: Found {len(parser.text_content)} text nodes ({len(all_text)} chars)")
    
    # Test 5: Check for known UI elements
    print("\n[5/5] Verifying dashboard UI elements...")
    required_patterns = [
        ('Welcome Back', 'Login page heading'),
        ('Sign in', 'Login action'),
        ('Email', 'Email field'),
        ('Password', 'Password field'),
    ]
    
    found_patterns = []
    missing_patterns = []
    
    html_lower = html_content.lower()
    for pattern, description in required_patterns:
        if pattern.lower() in html_lower:
            found_patterns.append((pattern, description))
        else:
            missing_patterns.append((pattern, description))
    
    if len(found_patterns) < 2:
        print(f"❌ FAIL: Dashboard UI not rendering properly")
        print(f"   Found: {[p[0] for p in found_patterns]}")
        print(f"   Missing: {[p[0] for p in missing_patterns]}")
        return False
    
    print(f"✅ PASS: Found {len(found_patterns)}/{len(required_patterns)} UI elements")
    for pattern, desc in found_patterns:
        print(f"   ✓ {pattern} ({desc})")
    
    return True


def main():
    """Main test execution"""
    print(f"Testing: {PRODUCTION_URL}")
    print(f"Timeout: {TIMEOUT}s")
    print()
    
    try:
        success = test_dashboard_renders()
        
        print()
        print("=" * 60)
        if success:
            print("✅ ALL TESTS PASSED - Dashboard renders correctly")
            print("=" * 60)
            print()
            print("Dashboard is healthy:")
            print(f"  - URL: {PRODUCTION_URL}")
            print("  - Status: ✅ Renders visible UI")
            print("  - White screen: ❌ Not detected")
            print("  - UI elements: ✅ Present")
            sys.exit(0)
        else:
            print("❌ TESTS FAILED - White screen or render failure detected")
            print("=" * 60)
            print()
            print("🚨 DEPLOYMENT BLOCKED 🚨")
            print()
            print("The dashboard is NOT rendering properly.")
            print("Possible causes:")
            print("  1. Client-side JavaScript error")
            print("  2. Hydration failure")
            print("  3. CSS loading issue")
            print("  4. Missing React root")
            print()
            print("Action required:")
            print("  - Check browser console for errors")
            print("  - Check container logs: docker logs dashboard_nextjs_prod")
            print("  - Verify NODE_ENV=production")
            print("  - Test locally: npm run build && npm start")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
