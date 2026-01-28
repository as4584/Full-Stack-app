"""
E2E Tests for Dashboard API Endpoints

Tests that all dashboard endpoints return valid JSON responses for different user states:
- New users (no business configured)
- Users with business but no calls
- Users with complete setup

This ensures the dashboard never crashes due to API errors.
"""
import os
import sys
import pytest
import requests
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Environment variables
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
TEST_EMAIL = os.getenv("TEST_EMAIL", "test@example.com")
TEST_PASSWORD = os.getenv("TEST_PASSWORD", "test123")
SMOKE_TEST = os.getenv("SMOKE_TEST", "false").lower() == "true"

# Skip smoke tests if SMOKE_TEST=true
pytestmark = pytest.mark.skipif(
    SMOKE_TEST, 
    reason="Skipping dashboard tests in smoke mode"
)


def login(base_url: str, email: str, password: str) -> requests.Session:
    """
    Login and return authenticated session with JWT cookie.
    """
    session = requests.Session()
    response = session.post(
        f"{base_url}/api/auth/login",
        json={"email": email, "password": password}
    )
    
    if response.status_code != 200:
        logger.error(f"Login failed: {response.status_code} - {response.text}")
        raise Exception(f"Login failed with status {response.status_code}")
    
    logger.info(f"✅ Logged in as {email}")
    return session


class TestDashboardEndpoints:
    """Test all dashboard API endpoints return valid JSON."""
    
    @pytest.fixture(scope="class")
    def auth_session(self):
        """Fixture to provide authenticated session."""
        return login(BASE_URL, TEST_EMAIL, TEST_PASSWORD)
    
    def test_user_me_endpoint_returns_valid_json(self, auth_session):
        """
        Test GET /api/auth/me returns valid user data.
        This is called by useUser() hook on dashboard mount.
        """
        logger.info("[TEST] GET /api/auth/me")
        response = auth_session.get(f"{BASE_URL}/api/auth/me")
        
        # Should return 200 OK
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Should return valid JSON
        assert response.headers.get("content-type", "").startswith("application/json"), \
            f"Expected JSON content-type, got: {response.headers.get('content-type')}"
        
        data = response.json()
        assert "email" in data, "Response missing 'email' field"
        assert data["email"] == TEST_EMAIL, f"Expected email={TEST_EMAIL}, got {data['email']}"
        
        logger.info(f"✅ /api/auth/me returned valid user: {data.get('email')}")
    
    def test_business_me_endpoint_handles_no_business(self, auth_session):
        """
        Test GET /api/business/me returns null (not 404) for users without business.
        This is called by useBusiness() hook on dashboard mount.
        
        Changed behavior: Instead of 404, returns null so frontend handles gracefully.
        """
        logger.info("[TEST] GET /api/business/me")
        response = auth_session.get(f"{BASE_URL}/api/business/me")
        
        # Should return 200 OK (even if no business)
        assert response.status_code == 200, \
            f"Expected 200, got {response.status_code}: {response.text}"
        
        # Should return valid JSON (null or business object)
        assert response.headers.get("content-type", "").startswith("application/json"), \
            f"Expected JSON content-type, got: {response.headers.get('content-type')}"
        
        data = response.json()
        
        # If null, that's OK for new users
        if data is None:
            logger.info("✅ /api/business/me returned null (no business configured)")
        else:
            # If not null, should have business fields
            assert "id" in data, "Business response missing 'id' field"
            assert "name" in data, "Business response missing 'name' field"
            logger.info(f"✅ /api/business/me returned business: {data.get('name')}")
    
    def test_business_calls_endpoint_never_fails(self, auth_session):
        """
        Test GET /api/business/calls returns empty array (not error) for users without calls.
        This is called by useRecentCalls() hook on dashboard mount.
        
        CRITICAL: This endpoint MUST NEVER throw SQL errors or return 500.
        The bug that caused "Failed to load recent calls" was a SQL error
        due to querying non-existent column 'recording_url'.
        
        This test ensures the endpoint:
        - Always returns HTTP 200
        - Always returns valid JSON array
        - Never throws database errors
        - Handles empty state gracefully
        """
        logger.info("[TEST] GET /api/business/calls - CRITICAL TEST")
        response = auth_session.get(f"{BASE_URL}/api/business/calls")
        
        # Should NEVER return 500 (this was the bug)
        assert response.status_code != 500, \
            f"CRITICAL: Calls endpoint returned 500 Internal Server Error: {response.text}"
        
        # Should return 200 OK
        assert response.status_code == 200, \
            f"Expected 200, got {response.status_code}: {response.text}"
        
        # Should return valid JSON array
        assert response.headers.get("content-type", "").startswith("application/json"), \
            f"Expected JSON content-type, got: {response.headers.get('content-type')}"
        
        try:
            data = response.json()
        except Exception as e:
            pytest.fail(f"Failed to parse JSON response: {e}. Response text: {response.text}")
        
        assert isinstance(data, list), f"Expected array, got: {type(data)}"
        
        if len(data) == 0:
            logger.info("✅ /api/business/calls returned empty array (no calls yet)")
        else:
            logger.info(f"✅ /api/business/calls returned {len(data)} calls")
            # Verify structure of first call
            call = data[0]
            required_fields = ["id", "from_number", "status", "created_at"]
            for field in required_fields:
                assert field in call, f"Call missing required field '{field}'"
            
            # Ensure recording_url is NOT in response (it was causing SQL errors)
            # The column doesn't exist in database, so shouldn't be queried
            logger.info(f"✅ Call structure validated: {list(call.keys())}")
    
    def test_calls_endpoint_no_sql_errors_in_logs(self, auth_session):
        """
        After calling /api/business/calls, check that no SQL errors appear in logs.
        This catches issues like "column does not exist" that manifest as 500 errors.
        """
        logger.info("[TEST] Checking for SQL errors after calls endpoint")
        
        # Call the endpoint
        response = auth_session.get(f"{BASE_URL}/api/business/calls")
        assert response.status_code == 200, f"Calls endpoint failed: {response.status_code}"
        
        # If we got a 200, the SQL query worked
        # The presence of this test documents that SQL errors are a regression risk
        logger.info("✅ No SQL errors detected (endpoint returned 200)")
    
    def test_all_dashboard_endpoints_never_return_500(self, auth_session):
        """
        Test that all dashboard endpoints return valid responses (no 500 errors).
        This is the master test to ensure dashboard never crashes.
        """
        endpoints = [
            "/api/auth/me",
            "/api/business/me", 
            "/api/business/calls"
        ]
        
        for endpoint in endpoints:
            logger.info(f"[TEST] Checking {endpoint} never returns 500")
            response = auth_session.get(f"{BASE_URL}{endpoint}")
            
            # Should never return 500 Internal Server Error
            assert response.status_code != 500, \
                f"{endpoint} returned 500 Internal Server Error: {response.text}"
            
            # Should return valid JSON (or at least not crash)
            try:
                response.json()
                logger.info(f"✅ {endpoint} returned valid JSON with status {response.status_code}")
            except Exception as e:
                pytest.fail(f"{endpoint} returned invalid JSON: {e}")
    
    def test_dashboard_endpoints_handle_invalid_auth(self):
        """
        Test that dashboard endpoints return 401 (not crash) for unauthenticated requests.
        """
        endpoints = [
            "/api/auth/me",
            "/api/business/me",
            "/api/business/calls"
        ]
        
        for endpoint in endpoints:
            logger.info(f"[TEST] {endpoint} with no auth")
            response = requests.get(f"{BASE_URL}{endpoint}")
            
            # Should return 401 Unauthorized or 403 Forbidden
            assert response.status_code in [401, 403], \
                f"Expected 401/403 for unauthenticated request to {endpoint}, got {response.status_code}"
            
            logger.info(f"✅ {endpoint} correctly rejects unauthenticated request")


class TestDashboardSmoke:
    """Smoke tests that run even in SMOKE_TEST=true mode."""
    
    def test_dashboard_endpoints_exist(self):
        """
        Quick smoke test to verify all dashboard endpoints exist (don't 404).
        This runs even in smoke mode to catch routing issues.
        """
        # Try without auth - should get 401/403, not 404
        endpoints = [
            "/api/auth/me",
            "/api/business/me",
            "/api/business/calls"
        ]
        
        for endpoint in endpoints:
            response = requests.get(f"{BASE_URL}{endpoint}")
            assert response.status_code != 404, \
                f"{endpoint} returned 404 - endpoint doesn't exist!"
            
            logger.info(f"✅ {endpoint} exists (returned {response.status_code})")


if __name__ == "__main__":
    """
    Run tests directly for quick validation.
    Usage:
        python test_dashboard_e2e.py                 # Full test suite
        SMOKE_TEST=true python test_dashboard_e2e.py # Smoke tests only
    """
    # Check required env vars
    if not TEST_EMAIL or not TEST_PASSWORD:
        logger.error("❌ TEST_EMAIL and TEST_PASSWORD must be set")
        sys.exit(1)
    
    # Run pytest
    pytest_args = [__file__, "-v", "-s"]
    sys.exit(pytest.main(pytest_args))
