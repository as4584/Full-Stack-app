#!/usr/bin/env python3
"""
Calendar Integration E2E Test
==============================

Tests Google Calendar OAuth integration flow end-to-end.

Exit Codes (CI-friendly):
    0 - All tests passed
    1 - Authentication failed (invalid credentials or JWT)
    2 - Fetch calendar state failed (API unreachable or 500 error)
    3 - OAuth availability check failed (unexpected response)
    4 - Calendar state inconsistent (field validation failed)
    5 - Unexpected error (catch-all for network/parsing issues)

Usage:
    # Full test (validates all fields)
    python3 test_calendar_e2e.py --url https://receptionist.lexmakesit.com
    
    # Smoke test (fast verification, skips deep checks)
    SMOKE_TEST=true python3 test_calendar_e2e.py --url https://receptionist.lexmakesit.com
    python3 test_calendar_e2e.py --smoke --url https://receptionist.lexmakesit.com
    
    # Local testing
    python3 test_calendar_e2e.py --url http://localhost:8001

Environment Variables:
    SMOKE_TEST - Set to 'true', '1', or 'yes' to enable smoke test mode
    
Smoke Test Mode:
    - Verifies login works (JWT obtained)
    - Verifies calendar state can be fetched
    - Verifies OAuth availability check returns proper response
    - Skips deep field validation
    - Completes in <10 seconds
    - Still fails with non-zero exit code on any error
"""

import os
import sys
import argparse
import requests
import json
import bcrypt
from typing import Dict, Any, Optional
from datetime import datetime

# Smoke test mode detection
SMOKE_TEST_MODE = os.getenv('SMOKE_TEST', '').lower() in ('true', '1', 'yes')

# Test credentials (same as settings test for consistency)
TEST_EMAIL = "thegamermasterninja@gmail.com"
TEST_PASSWORD = "Alexander1221"


class CalendarE2ETest:
    """
    End-to-end test for Google Calendar integration.
    
    Tests the full OAuth availability check flow and calendar connection state.
    Validates that calendar integration is truly OPTIONAL and doesn't block
    core functionality.
    """
    
    def __init__(self, base_url: str, smoke_mode: bool = False):
        """
        Initialize test suite.
        
        Args:
            base_url: Base URL of the API (e.g., https://receptionist.lexmakesit.com)
            smoke_mode: If True, skip deep field validation (fast smoke test)
        """
        self.base_url = base_url.rstrip('/')
        self.smoke_mode = smoke_mode
        self.jwt_token: Optional[str] = None
        self.business_id: Optional[str] = None
        self.session = requests.Session()
        
        if self.smoke_mode:
            print("🚀 SMOKE TEST MODE ENABLED - Skipping deep validation checks")
    
    def _log_phase(self, phase: int, title: str):
        """Print phase header."""
        print(f"\n{'=' * 80}")
        print(f"Phase {phase}: {title}")
        print('=' * 80)
    
    def _log_success(self, message: str):
        """Print success message."""
        print(f"✅ {message}")
    
    def _log_error(self, message: str):
        """Print error message."""
        print(f"❌ {message}")
    
    def _log_info(self, message: str):
        """Print info message."""
        print(f"ℹ️  {message}")
    
    def test_login(self) -> bool:
        """
        Phase 1: Test authentication and JWT retrieval.
        
        Returns:
            True if login successful and JWT obtained
            False otherwise (exits with code 1)
        """
        self._log_phase(1, "Authentication")
        
        try:
            url = f"{self.base_url}/api/auth/login"
            payload = {
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
            
            self._log_info(f"POST {url}")
            self._log_info(f"Payload: {json.dumps({'email': TEST_EMAIL, 'password': '***'})}")
            
            response = self.session.post(url, json=payload, timeout=10)
            
            self._log_info(f"Response Status: {response.status_code}")
            
            if response.status_code != 200:
                self._log_error(f"Login failed with status {response.status_code}")
                self._log_error(f"Response: {response.text}")
                sys.exit(1)
            
            data = response.json()
            
            # Extract JWT token
            if 'access_token' not in data:
                self._log_error("No access_token in response")
                self._log_error(f"Response keys: {list(data.keys())}")
                sys.exit(1)
            
            self.jwt_token = data['access_token']
            self._log_success(f"JWT token obtained: {self.jwt_token[:20]}...")
            
            # Extract business ID if available
            if 'business_id' in data:
                self.business_id = str(data['business_id'])
                self._log_info(f"Business ID from login: {self.business_id}")
            
            return True
            
        except requests.RequestException as e:
            self._log_error(f"Network error during login: {e}")
            sys.exit(1)
        except Exception as e:
            self._log_error(f"Unexpected error during login: {e}")
            sys.exit(1)
    
    def test_fetch_calendar_state(self) -> Dict[str, Any]:
        """
        Phase 2: Fetch current calendar connection state from business profile.
        
        Returns:
            Business data dict containing calendar state
            Exits with code 2 if fetch fails
        """
        self._log_phase(2, "Fetch Calendar State")
        
        try:
            url = f"{self.base_url}/api/business/me"
            headers = {"Authorization": f"Bearer {self.jwt_token}"}
            
            self._log_info(f"GET {url}")
            self._log_info(f"Headers: Authorization: Bearer {self.jwt_token[:20]}...")
            
            response = self.session.get(url, headers=headers, timeout=10)
            
            self._log_info(f"Response Status: {response.status_code}")
            
            if response.status_code != 200:
                self._log_error(f"Fetch failed with status {response.status_code}")
                self._log_error(f"Response: {response.text}")
                sys.exit(2)
            
            business = response.json()
            
            # Validate calendar field exists
            if 'google_calendar_connected' not in business:
                self._log_error("google_calendar_connected field missing from business profile")
                self._log_error(f"Available fields: {list(business.keys())}")
                sys.exit(2)
            
            calendar_connected = business.get('google_calendar_connected', False)
            self._log_success(f"Calendar state fetched: {'CONNECTED' if calendar_connected else 'NOT CONNECTED'}")
            
            # Extract business ID if we don't have it
            if not self.business_id and 'id' in business:
                self.business_id = str(business['id'])
                self._log_info(f"Business ID from profile: {self.business_id}")
            
            return business
            
        except requests.RequestException as e:
            self._log_error(f"Network error during fetch: {e}")
            sys.exit(2)
        except Exception as e:
            self._log_error(f"Unexpected error during fetch: {e}")
            sys.exit(2)
    
    def test_oauth_availability(self) -> Dict[str, Any]:
        """
        Phase 3: Test OAuth availability check endpoint.
        
        Verifies that /oauth/google/start returns proper response:
        - If OAuth configured: HTTP 302 redirect OR HTTP 200
        - If OAuth NOT configured: HTTP 200 with JSON {available: false, error: "..."}
        
        Returns:
            Dict with availability info
            Exits with code 3 if check fails unexpectedly
        """
        self._log_phase(3, "OAuth Availability Check")
        
        if not self.business_id:
            self._log_error("No business_id available for OAuth check")
            sys.exit(3)
        
        try:
            url = f"{self.base_url}/oauth/google/start?business_id={self.business_id}"
            
            self._log_info(f"GET {url}")
            self._log_info("Testing OAuth availability without following redirects...")
            
            # Don't follow redirects - we want to see the actual response
            response = self.session.get(url, allow_redirects=False, timeout=10)
            
            self._log_info(f"Response Status: {response.status_code}")
            self._log_info(f"Content-Type: {response.headers.get('content-type', 'N/A')}")
            
            # Case 1: OAuth is configured - expect redirect (302)
            if response.status_code == 302:
                location = response.headers.get('Location', '')
                self._log_success("OAuth IS CONFIGURED - Got redirect to Google OAuth")
                self._log_info(f"Redirect location: {location[:80]}...")
                return {"available": True, "status": "configured", "redirect_url": location}
            
            # Case 2: OAuth not configured - expect JSON response
            elif response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                
                if 'application/json' in content_type:
                    data = response.json()
                    
                    if data.get('available') is False:
                        error_msg = data.get('error', 'No error message')
                        detail = data.get('detail', '')
                        self._log_success("OAuth NOT CONFIGURED (expected in dev/staging)")
                        self._log_info(f"Error message: {error_msg}")
                        if detail:
                            self._log_info(f"Detail: {detail}")
                        return {"available": False, "status": "not_configured", "error": error_msg}
                    else:
                        # Unexpected: JSON but available=True without redirect?
                        self._log_error("Unexpected: JSON response with available=True but no redirect")
                        self._log_error(f"Response: {json.dumps(data, indent=2)}")
                        sys.exit(3)
                else:
                    # HTTP 200 but not JSON - assume OAuth available
                    self._log_success("OAuth appears available (HTTP 200, non-JSON response)")
                    return {"available": True, "status": "available"}
            
            # Case 3: Unexpected status code
            else:
                self._log_error(f"Unexpected status code: {response.status_code}")
                self._log_error(f"Response: {response.text[:200]}")
                sys.exit(3)
                
        except requests.RequestException as e:
            self._log_error(f"Network error during OAuth check: {e}")
            sys.exit(3)
        except Exception as e:
            self._log_error(f"Unexpected error during OAuth check: {e}")
            sys.exit(3)
    
    def test_calendar_state_consistency(self, business: Dict[str, Any], oauth_info: Dict[str, Any]):
        """
        Phase 4: Validate calendar state consistency.
        
        Ensures that:
        - If calendar connected in profile, OAuth must be configured
        - If OAuth not configured, calendar should not be connected
        - Calendar field is a boolean
        
        In smoke mode: Just verify the field exists and is boolean
        
        Args:
            business: Business profile data from Phase 2
            oauth_info: OAuth availability data from Phase 3
        """
        self._log_phase(4, "Calendar State Validation")
        
        calendar_connected = business.get('google_calendar_connected', False)
        oauth_available = oauth_info.get('available', False)
        
        # Check 1: Field type validation
        if not isinstance(calendar_connected, bool):
            self._log_error(f"google_calendar_connected is not a boolean: {type(calendar_connected)}")
            sys.exit(4)
        
        self._log_success(f"✓ google_calendar_connected is valid boolean: {calendar_connected}")
        
        if self.smoke_mode:
            self._log_info("SMOKE MODE: Skipping deep consistency checks")
            return
        
        # Check 2: Consistency validation (only in full mode)
        if calendar_connected and not oauth_available:
            self._log_error("INCONSISTENCY: Calendar marked as connected but OAuth is not available")
            self._log_error("This should not happen - calendar_connected should be false if OAuth unavailable")
            sys.exit(4)
        
        self._log_success("✓ Calendar state is consistent with OAuth availability")
        
        # Check 3: Additional field validation
        if calendar_connected:
            # If connected, there might be additional fields like calendar_id, google_email
            if 'google_email' in business:
                self._log_info(f"Connected Google account: {business.get('google_email', 'N/A')}")
            if 'calendar_id' in business:
                self._log_info(f"Calendar ID: {business.get('calendar_id', 'N/A')}")
        
        self._log_success("✓ All calendar state validations passed")
    
    def run_full_test(self) -> int:
        """
        Run the complete calendar E2E test suite.
        
        Returns:
            0 if all tests pass
            1-5 if specific test phase fails (see exit codes at top of file)
        """
        mode_str = "SMOKE" if self.smoke_mode else "FULL E2E"
        print("\n" + "=" * 80)
        print(f"{'CALENDAR INTEGRATION ' + mode_str + ' TEST':^80}")
        print("=" * 80)
        print(f"Target: {self.base_url}")
        print(f"Mode: {mode_str} {'(fast, skips deep checks)' if self.smoke_mode else '(thorough, validates all fields)'}")
        print(f"Time: {datetime.now().isoformat()}")
        print("=" * 80)
        
        try:
            # Phase 1: Authentication
            self.test_login()
            
            # Phase 2: Fetch calendar state
            business = self.test_fetch_calendar_state()
            
            # Phase 3: OAuth availability check
            oauth_info = self.test_oauth_availability()
            
            # Phase 4: State validation
            self.test_calendar_state_consistency(business, oauth_info)
            
            # All phases passed
            print("\n" + "=" * 80)
            print("✅ ALL CALENDAR TESTS PASSED")
            print("=" * 80)
            print(f"Business ID: {self.business_id}")
            print(f"Calendar Connected: {business.get('google_calendar_connected', False)}")
            print(f"OAuth Available: {oauth_info.get('available', False)}")
            if not oauth_info.get('available'):
                print(f"OAuth Status: {oauth_info.get('error', 'Not configured')}")
            print("=" * 80)
            
            return 0
            
        except SystemExit as e:
            # Re-raise exit codes from test phases
            return e.code
        except Exception as e:
            # Unexpected error (exit code 5)
            print("\n" + "=" * 80)
            print("❌ UNEXPECTED ERROR")
            print("=" * 80)
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            print("=" * 80)
            return 5


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Calendar Integration E2E Test",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full test (thorough validation)
  python3 test_calendar_e2e.py --url https://receptionist.lexmakesit.com
  
  # Smoke test (fast verification)
  SMOKE_TEST=true python3 test_calendar_e2e.py --url https://receptionist.lexmakesit.com
  python3 test_calendar_e2e.py --smoke --url https://receptionist.lexmakesit.com
  
  # Local testing
  python3 test_calendar_e2e.py --url http://localhost:8001

Exit Codes:
  0 = All tests passed
  1 = Authentication failed
  2 = Fetch calendar state failed
  3 = OAuth availability check failed
  4 = Calendar state inconsistent
  5 = Unexpected error
        """
    )
    
    parser.add_argument(
        '--url',
        required=True,
        help='Base URL of the API (e.g., https://receptionist.lexmakesit.com)'
    )
    
    parser.add_argument(
        '--smoke',
        action='store_true',
        help='Enable smoke test mode (fast, skips deep validation)'
    )
    
    args = parser.parse_args()
    
    # Determine smoke mode from CLI flag or environment variable
    smoke_mode = args.smoke or SMOKE_TEST_MODE
    
    # Use credentials from CLI or defaults
    email = args.email if hasattr(args, 'email') else TEST_EMAIL
    password = args.password if hasattr(args, 'password') else TEST_PASSWORD
    
    # Run tests
    tester = CalendarE2ETest(base_url=args.url, smoke_mode=smoke_mode)
    # Note: CalendarE2ETest uses global TEST_EMAIL and TEST_PASSWORD
    # CLI args for email/password can be added later if needed
    exit_code = tester.run_full_test()
    
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
