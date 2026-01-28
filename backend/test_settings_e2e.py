#!/usr/bin/env python3
"""
Automated End-to-End Settings Persistence Test

This script verifies that settings can be saved and retrieved correctly
for any user in the AI Receptionist SaaS platform.

USAGE:
    python test_settings_e2e.py [--url https://api.example.com]

REQUIREMENTS:
    - Valid user credentials
    - Backend API running
    - Database accessible

TEST FLOW:
    1. Login (JWT authentication)
    2. Fetch current settings
    3. Update settings with test data
    4. Verify immediate response
    5. Fetch settings again to confirm persistence
    6. Fail loudly with clear diagnostics on any error

EXIT CODES:
    0 - All tests passed
    1 - Auth failed
    2 - Fetch failed
    3 - Save failed
    4 - Persistence verification failed
    5 - Invalid response data
"""

import sys
import json
import logging
import argparse
import os
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import requests
from requests.exceptions import RequestException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Check if running in smoke test mode
SMOKE_TEST_MODE = os.getenv('SMOKE_TEST', '').lower() in ('true', '1', 'yes')

# Test configuration
TEST_USER_EMAIL = "thegamermasterninja@gmail.com"
TEST_USER_PASSWORD = "Alexander1221"

# Expected settings to apply
TEST_SETTINGS = {
    "name": "Lex Makes It",
    "industry": "Software Development, Website Development",
    "common_services": "Software Development, Website Development",
    "business_hours": "Monday-Friday, 12:00 PM - 10:00 PM",
    "description": "We provide software development and website development services. For more information, visit lexmakesit.com."
}


class SettingsTestResult:
    """Container for test results with diagnostic information."""
    
    def __init__(self, phase: str, success: bool, message: str, data: Optional[Dict] = None):
        self.phase = phase
        self.success = success
        self.message = message
        self.data = data or {}
        self.timestamp = datetime.now().isoformat()
    
    def __repr__(self):
        status = "✅ PASS" if self.success else "❌ FAIL"
        return f"{status} | {self.phase}: {self.message}"


class SettingsE2ETest:
    """End-to-end test for settings persistence."""
    
    def __init__(self, base_url: str, smoke_mode: bool = False):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.jwt_token: Optional[str] = None
        self.business_id: Optional[str] = None
        self.results: list[SettingsTestResult] = []
        self.smoke_mode = smoke_mode
        
        if self.smoke_mode:
            logger.info("🚀 SMOKE TEST MODE ENABLED - Running fast verification")
    
    def log_result(self, result: SettingsTestResult):
        """Log and store a test result."""
        self.results.append(result)
        logger.info(str(result))
        if not result.success:
            logger.error(f"Details: {json.dumps(result.data, indent=2)}")
    
    def make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        use_auth: bool = False
    ) -> Tuple[int, Dict[str, Any]]:
        """
        Make HTTP request with proper error handling.
        
        Returns:
            Tuple of (status_code, response_json)
        """
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if use_auth and self.jwt_token:
            headers["Authorization"] = f"Bearer {self.jwt_token}"
        
        try:
            logger.info(f"{method} {url}")
            if data:
                logger.debug(f"Request body: {json.dumps(data, indent=2)}")
            
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                headers=headers,
                timeout=30
            )
            
            logger.info(f"Response: {response.status_code}")
            
            # Try to parse JSON response
            try:
                response_data = response.json()
                logger.debug(f"Response body: {json.dumps(response_data, indent=2)}")
            except json.JSONDecodeError:
                response_data = {
                    "raw_text": response.text[:500],
                    "error": "Failed to parse JSON response"
                }
            
            return response.status_code, response_data
            
        except RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            return 0, {"error": str(e)}
    
    def test_login(self) -> bool:
        """
        PHASE 1: Test user authentication.
        
        Returns:
            True if login successful, False otherwise
        """
        logger.info("=" * 70)
        logger.info("PHASE 1: AUTHENTICATION")
        logger.info("=" * 70)
        
        status_code, response = self.make_request(
            "POST",
            "/api/auth/login",
            data={
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            }
        )
        
        # Check HTTP status
        if status_code != 200:
            self.log_result(SettingsTestResult(
                phase="Authentication",
                success=False,
                message=f"Login failed with status {status_code}",
                data=response
            ))
            return False
        
        # Check JWT token presence
        if "access_token" not in response:
            self.log_result(SettingsTestResult(
                phase="Authentication",
                success=False,
                message="No access_token in response",
                data=response
            ))
            return False
        
        self.jwt_token = response["access_token"]
        
        # Extract user info
        if "user" in response:
            user = response["user"]
            logger.info(f"Logged in as: {user.get('email')} (ID: {user.get('id')})")
            if user.get('business_id'):
                self.business_id = str(user['business_id'])
        
        self.log_result(SettingsTestResult(
            phase="Authentication",
            success=True,
            message="Login successful, JWT token received",
            data={"token_length": len(self.jwt_token)}
        ))
        
        return True
    
    def test_fetch_settings(self) -> Optional[Dict[str, Any]]:
        """
        PHASE 2: Fetch current settings.
        
        Returns:
            Current settings dict if successful, None otherwise
        """
        logger.info("=" * 70)
        logger.info("PHASE 2: FETCH CURRENT SETTINGS")
        logger.info("=" * 70)
        
        status_code, response = self.make_request(
            "GET",
            "/api/business/me",
            use_auth=True
        )
        
        if status_code != 200:
            self.log_result(SettingsTestResult(
                phase="Fetch Settings",
                success=False,
                message=f"Failed to fetch settings (HTTP {status_code})",
                data=response
            ))
            return None
        
        # Validate response structure
        required_fields = ["id", "name"]
        missing_fields = [f for f in required_fields if f not in response]
        
        if missing_fields:
            self.log_result(SettingsTestResult(
                phase="Fetch Settings",
                success=False,
                message=f"Missing required fields: {missing_fields}",
                data=response
            ))
            return None
        
        if response.get("id"):
            self.business_id = str(response["id"])
        
        logger.info(f"Current settings for business {self.business_id}:")
        logger.info(f"  - Name: {response.get('name')}")
        logger.info(f"  - Industry: {response.get('industry')}")
        logger.info(f"  - Hours: {response.get('business_hours')}")
        logger.info(f"  - Phone: {response.get('phone_number')}")
        logger.info(f"  - Receptionist: {response.get('receptionist_enabled')}")
        
        self.log_result(SettingsTestResult(
            phase="Fetch Settings",
            success=True,
            message=f"Successfully fetched settings for business {self.business_id}",
            data={"business_id": self.business_id}
        ))
        
        return response
    
    def test_update_settings(self) -> Optional[Dict[str, Any]]:
        """
        PHASE 3: Update settings with test data.
        
        Returns:
            Updated settings dict if successful, None otherwise
        """
        logger.info("=" * 70)
        logger.info("PHASE 3: UPDATE SETTINGS")
        logger.info("=" * 70)
        
        logger.info("Applying test settings:")
        for key, value in TEST_SETTINGS.items():
            logger.info(f"  - {key}: {value}")
        
        status_code, response = self.make_request(
            "PUT",
            "/api/business/me",
            data=TEST_SETTINGS,
            use_auth=True
        )
        
        if status_code != 200:
            self.log_result(SettingsTestResult(
                phase="Update Settings",
                success=False,
                message=f"Failed to update settings (HTTP {status_code})",
                data=response
            ))
            return None
        
        # Check if update was acknowledged
        if response.get("status") in ["success", "audit_pending"]:
            logger.info(f"Update acknowledged: {response.get('status')}")
        
        self.log_result(SettingsTestResult(
            phase="Update Settings",
            success=True,
            message="Settings update request successful",
            data=response
        ))
        
        return response
    
    def test_verify_persistence(self, expected_settings: Dict[str, Any]) -> bool:
        """
        PHASE 4: Verify settings persisted correctly.
        
        Args:
            expected_settings: Settings that should be persisted
            
        Returns:
            True if all settings match, False otherwise
        """
        logger.info("=" * 70)
        logger.info("PHASE 4: VERIFY PERSISTENCE")
        logger.info("=" * 70)
        
        # Fetch settings again
        status_code, response = self.make_request(
            "GET",
            "/api/business/me",
            use_auth=True
        )
        
        if status_code != 200:
            self.log_result(SettingsTestResult(
                phase="Verify Persistence",
                success=False,
                message=f"Failed to re-fetch settings (HTTP {status_code})",
                data=response
            ))
            return False
        
        # Compare each expected field
        mismatches = []
        for key, expected_value in expected_settings.items():
            actual_value = response.get(key)
            
            if actual_value != expected_value:
                mismatches.append({
                    "field": key,
                    "expected": expected_value,
                    "actual": actual_value
                })
                logger.warning(f"Mismatch in '{key}':")
                logger.warning(f"  Expected: {expected_value}")
                logger.warning(f"  Actual:   {actual_value}")
            else:
                logger.info(f"✓ {key}: {actual_value}")
        
        if mismatches:
            self.log_result(SettingsTestResult(
                phase="Verify Persistence",
                success=False,
                message=f"Settings did not persist correctly ({len(mismatches)} mismatches)",
                data={"mismatches": mismatches}
            ))
            return False
        
        self.log_result(SettingsTestResult(
            phase="Verify Persistence",
            success=True,
            message="All settings persisted correctly",
            data={"verified_fields": list(expected_settings.keys())}
        ))
        
        return True
    
    def run_full_test(self) -> int:
        """
        Run complete end-to-end test suite.
        
        Returns:
            Exit code (0 = success, non-zero = failure)
        """
        test_mode = "SMOKE TEST" if self.smoke_mode else "FULL E2E TEST"
        
        logger.info("")
        logger.info("╔" + "═" * 68 + "╗")
        logger.info("║" + f" SETTINGS PERSISTENCE {test_mode} ".center(68) + "║")
        logger.info("╚" + "═" * 68 + "╝")
        logger.info(f"Base URL: {self.base_url}")
        logger.info(f"Test User: {TEST_USER_EMAIL}")
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        if self.smoke_mode:
            logger.info("Mode: SMOKE (fast, skips deep checks)")
        logger.info("")
        
        # PHASE 1: Authentication
        if not self.test_login():
            logger.error("CRITICAL: Authentication failed")
            return 1
        
        # PHASE 2: Fetch current settings
        current_settings = self.test_fetch_settings()
        if current_settings is None:
            logger.error("CRITICAL: Failed to fetch settings")
            return 2
        
        # PHASE 3: Update settings
        update_response = self.test_update_settings()
        if update_response is None:
            logger.error("CRITICAL: Failed to update settings")
            return 3
        
        # PHASE 4: Verify persistence (simplified in smoke mode)
        if self.smoke_mode:
            # In smoke mode, just verify we can fetch again
            logger.info("=" * 70)
            logger.info("PHASE 4: VERIFY FETCH (Smoke Mode)")
            logger.info("=" * 70)
            status_code, response = self.make_request(
                "GET",
                "/api/business/me",
                use_auth=True
            )
            if status_code != 200:
                self.log_result(SettingsTestResult(
                    phase="Verify Fetch",
                    success=False,
                    message="Failed to re-fetch after save",
                    data={"status_code": status_code}
                ))
                logger.error("CRITICAL: Settings fetch after save failed")
                return 4
            
            self.log_result(SettingsTestResult(
                phase="Verify Fetch",
                success=True,
                message="Settings re-fetch successful (smoke mode)",
                data={}
            ))
        else:
            # Full mode: verify all fields match
            if not self.test_verify_persistence(TEST_SETTINGS):
                logger.error("CRITICAL: Settings did not persist")
                return 4
        
        # Success summary
        logger.info("")
        logger.info("=" * 70)
        logger.info("TEST SUMMARY")
        logger.info("=" * 70)
        
        passed = sum(1 for r in self.results if r.success)
        failed = sum(1 for r in self.results if not r.success)
        
        logger.info(f"Total phases: {len(self.results)}")
        logger.info(f"Passed: {passed}")
        logger.info(f"Failed: {failed}")
        logger.info("")
        
        if failed == 0:
            logger.info("╔" + "═" * 68 + "╗")
            logger.info("║" + " ✅ ALL TESTS PASSED ".center(68) + "║")
            logger.info("╚" + "═" * 68 + "╝")
            return 0
        else:
            logger.error("╔" + "═" * 68 + "╗")
            logger.error("║" + " ❌ TESTS FAILED ".center(68) + "║")
            logger.error("╚" + "═" * 68 + "╝")
            return 5


def main():
    """Main entry point for the test script."""
    parser = argparse.ArgumentParser(
        description="Automated end-to-end test for settings persistence"
    )
    parser.add_argument(
        "--url",
        default="https://receptionist.lexmakesit.com",
        help="Base URL of the API (default: https://receptionist.lexmakesit.com)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Run in smoke test mode (fast, skips deep checks)"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Determine smoke mode from CLI flag or environment variable
    smoke_mode = args.smoke or SMOKE_TEST_MODE
    
    # Run the test
    test = SettingsE2ETest(base_url=args.url, smoke_mode=smoke_mode)
    exit_code = test.run_full_test()
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
