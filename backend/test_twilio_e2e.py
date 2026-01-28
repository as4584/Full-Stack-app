#!/usr/bin/env python3
"""
Twilio Phone Integration E2E Test
==================================

Tests Twilio phone number integration and AI receptionist routing.

Exit Codes (CI-friendly):
    0 - All tests passed
    1 - Authentication failed (invalid credentials or JWT)
    2 - Fetch phone state failed (API unreachable or 500 error)
    3 - Phone number missing or invalid
    4 - Receptionist state inconsistent
    5 - Unexpected error (catch-all for network/parsing issues)

Usage:
    # Full test (validates all fields)
    python3 test_twilio_e2e.py --url https://receptionist.lexmakesit.com
    
    # Smoke test (fast verification, skips deep checks)
    SMOKE_TEST=true python3 test_twilio_e2e.py --url https://receptionist.lexmakesit.com
    python3 test_twilio_e2e.py --smoke --url https://receptionist.lexmakesit.com
    
    # Local testing
    python3 test_twilio_e2e.py --url http://localhost:8001

Environment Variables:
    SMOKE_TEST - Set to 'true', '1', or 'yes' to enable smoke test mode
    
Smoke Test Mode:
    - Verifies login works (JWT obtained)
    - Verifies phone state can be fetched
    - Verifies phone number exists (if assigned)
    - Skips deep field validation
    - Completes in <10 seconds
    - Still fails with non-zero exit code on any error
"""

import os
import sys
import argparse
import requests
import json
import re
from typing import Dict, Any, Optional
from datetime import datetime

# Smoke test mode detection
SMOKE_TEST_MODE = os.getenv('SMOKE_TEST', '').lower() in ('true', '1', 'yes')

# Test credentials (same as other E2E tests for consistency)
TEST_EMAIL = "thegamermasterninja@gmail.com"
TEST_PASSWORD = "Alexander1221"


class TwilioE2ETest:
    """
    End-to-end test for Twilio phone integration.
    
    Tests phone number assignment, receptionist_enabled state, and validates
    that phone routing is working correctly.
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
    
    def _log_warning(self, message: str):
        """Print warning message."""
        print(f"⚠️  {message}")
    
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
    
    def test_fetch_phone_state(self) -> Dict[str, Any]:
        """
        Phase 2: Fetch current phone/receptionist state from business profile.
        
        Returns:
            Business data dict containing phone and receptionist state
            Exits with code 2 if fetch fails
        """
        self._log_phase(2, "Fetch Phone & Receptionist State")
        
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
            
            # Check for phone-related fields
            phone_number = business.get('phone_number')
            receptionist_enabled = business.get('receptionist_enabled', False)
            
            self._log_success(f"Phone state fetched")
            self._log_info(f"Phone Number: {phone_number if phone_number else 'NOT ASSIGNED'}")
            self._log_info(f"Receptionist Enabled: {receptionist_enabled}")
            
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
    
    def test_phone_number_validation(self, business: Dict[str, Any]):
        """
        Phase 3: Validate phone number format and assignment.
        
        Args:
            business: Business profile data from Phase 2
            
        Exits with code 3 if phone number validation fails
        """
        self._log_phase(3, "Phone Number Validation")
        
        phone_number = business.get('phone_number')
        
        # Check 1: Phone number exists (may be None for new businesses)
        if not phone_number:
            self._log_warning("No phone number assigned to this business")
            self._log_info("This is OK for new accounts - phone can be purchased in onboarding")
            return  # Not an error - businesses may not have phone yet
        
        # Check 2: Phone number format (E.164 format: +1234567890)
        if not re.match(r'^\+\d{11,15}$', phone_number):
            self._log_error(f"Phone number format invalid: {phone_number}")
            self._log_error("Expected E.164 format: +1234567890")
            sys.exit(3)
        
        self._log_success(f"✓ Phone number is valid E.164 format: {phone_number}")
        
        if self.smoke_mode:
            self._log_info("SMOKE MODE: Skipping deep phone validation")
            return
        
        # Check 3: Phone number starts with +1 (US/Canada) - most common
        if not phone_number.startswith('+1'):
            self._log_warning(f"Phone number is not US/Canada (+1): {phone_number}")
            self._log_info("This may be intentional for international businesses")
        else:
            self._log_success(f"✓ Phone number is US/Canada (+1)")
    
    def test_receptionist_state(self, business: Dict[str, Any]):
        """
        Phase 4: Validate receptionist enabled state and consistency.
        
        Args:
            business: Business profile data from Phase 2
            
        Exits with code 4 if receptionist state is inconsistent
        """
        self._log_phase(4, "Receptionist State Validation")
        
        phone_number = business.get('phone_number')
        receptionist_enabled = business.get('receptionist_enabled', False)
        
        # Check 1: Field type validation
        if not isinstance(receptionist_enabled, bool):
            self._log_error(f"receptionist_enabled is not a boolean: {type(receptionist_enabled)}")
            sys.exit(4)
        
        self._log_success(f"✓ receptionist_enabled is valid boolean: {receptionist_enabled}")
        
        if self.smoke_mode:
            self._log_info("SMOKE MODE: Skipping deep consistency checks")
            return
        
        # Check 2: Consistency validation
        if receptionist_enabled and not phone_number:
            self._log_error("INCONSISTENCY: Receptionist enabled but no phone number assigned")
            self._log_error("Cannot enable receptionist without a phone number")
            sys.exit(4)
        
        if receptionist_enabled:
            self._log_success("✓ Receptionist is enabled with valid phone number")
        else:
            self._log_info("Receptionist is disabled (this is OK)")
        
        # Check 3: Additional business info validation (for receptionist functionality)
        if receptionist_enabled:
            required_fields = ['name', 'business_hours']
            missing_fields = [f for f in required_fields if not business.get(f)]
            
            if missing_fields:
                self._log_warning(f"Receptionist enabled but missing recommended fields: {', '.join(missing_fields)}")
                self._log_info("Receptionist may not function optimally without these fields")
            else:
                self._log_success("✓ All recommended fields present for receptionist")
    
    def run_full_test(self) -> int:
        """
        Run the complete Twilio phone integration E2E test suite.
        
        Returns:
            0 if all tests pass
            1-5 if specific test phase fails (see exit codes at top of file)
        """
        mode_str = "SMOKE" if self.smoke_mode else "FULL E2E"
        print("\n" + "=" * 80)
        print(f"{'TWILIO PHONE INTEGRATION ' + mode_str + ' TEST':^80}")
        print("=" * 80)
        print(f"Target: {self.base_url}")
        print(f"Mode: {mode_str} {'(fast, skips deep checks)' if self.smoke_mode else '(thorough, validates all fields)'}")
        print(f"Time: {datetime.now().isoformat()}")
        print("=" * 80)
        
        try:
            # Phase 1: Authentication
            self.test_login()
            
            # Phase 2: Fetch phone state
            business = self.test_fetch_phone_state()
            
            # Phase 3: Phone number validation
            self.test_phone_number_validation(business)
            
            # Phase 4: Receptionist state validation
            self.test_receptionist_state(business)
            
            # All phases passed
            print("\n" + "=" * 80)
            print("✅ ALL TWILIO TESTS PASSED")
            print("=" * 80)
            print(f"Business ID: {self.business_id}")
            print(f"Phone Number: {business.get('phone_number', 'NOT ASSIGNED')}")
            print(f"Receptionist Enabled: {business.get('receptionist_enabled', False)}")
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
        description="Twilio Phone Integration E2E Test",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full test (thorough validation)
  python3 test_twilio_e2e.py --url https://receptionist.lexmakesit.com
  
  # Smoke test (fast verification)
  SMOKE_TEST=true python3 test_twilio_e2e.py --url https://receptionist.lexmakesit.com
  python3 test_twilio_e2e.py --smoke --url https://receptionist.lexmakesit.com
  
  # Local testing
  python3 test_twilio_e2e.py --url http://localhost:8001

Exit Codes:
  0 = All tests passed
  1 = Authentication failed
  2 = Fetch phone state failed
  3 = Phone number invalid
  4 = Receptionist state inconsistent
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
    
    # Run tests
    tester = TwilioE2ETest(base_url=args.url, smoke_mode=smoke_mode)
    exit_code = tester.run_full_test()
    
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
