#!/usr/bin/env python3
"""
AUTOMATED LOGIN VERIFICATION TOOL
==================================
Tests the complete authentication flow end-to-end.

VERIFICATION STEPS:
1. Call login endpoint with credentials
2. Validate HTTP response status
3. Parse and validate JWT token
4. Decode JWT and verify claims
5. Test protected endpoint access
6. Report detailed results

USAGE:
    python verify_login.py <email> <password> [--url https://api.example.com]

EXAMPLE:
    python verify_login.py thegamermasterninja@gmail.com Alexander1221
    python verify_login.py user@example.com pass123 --url https://receptionist.lexmakesit.com
"""

import sys
import os
import json
import logging
import requests
import jwt
from datetime import datetime
from typing import Dict, Optional, Tuple
from urllib.parse import urljoin

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_receptionist.config.settings import get_settings


class AuthVerificationResult:
    """Stores authentication verification results."""
    
    def __init__(self):
        self.steps = {}
        self.token = None
        self.decoded_token = None
        self.user_info = None
        self.errors = []
    
    def add_step(self, name: str, passed: bool, message: str, data: Optional[Dict] = None):
        """Add a verification step result."""
        self.steps[name] = {
            "passed": passed,
            "message": message,
            "data": data or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if passed:
            logger.info(f"✅ {name}: {message}")
        else:
            logger.error(f"❌ {name}: {message}")
            self.errors.append(f"{name}: {message}")
    
    def is_success(self) -> bool:
        """Check if all steps passed."""
        return all(step["passed"] for step in self.steps.values())
    
    def print_summary(self):
        """Print detailed summary."""
        logger.info("="*70)
        logger.info("AUTHENTICATION VERIFICATION SUMMARY")
        logger.info("="*70)
        
        for step_name, step_data in self.steps.items():
            status = "✅ PASS" if step_data["passed"] else "❌ FAIL"
            logger.info(f"{status} | {step_name}")
            logger.info(f"      {step_data['message']}")
        
        logger.info("="*70)
        if self.is_success():
            logger.info("OVERALL: ✅ AUTHENTICATION SUCCESSFUL")
        else:
            logger.error("OVERALL: ❌ AUTHENTICATION FAILED")
            logger.error("Errors:")
            for error in self.errors:
                logger.error(f"  - {error}")
        logger.info("="*70)


def test_login_endpoint(base_url: str, email: str, password: str) -> Tuple[bool, Dict]:
    """
    Test Step 1: Call login endpoint.
    
    Returns:
        (success, response_data)
    """
    login_url = urljoin(base_url, "/api/auth/login")
    logger.info(f"[LOGIN] Calling {login_url}")
    
    try:
        response = requests.post(
            login_url,
            json={"email": email, "password": password},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        logger.info(f"[LOGIN] HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"[LOGIN] Response keys: {list(data.keys())}")
            return True, data
        else:
            error_detail = response.text[:200]
            logger.error(f"[LOGIN] Error response: {error_detail}")
            return False, {"error": error_detail, "status": response.status_code}
            
    except requests.exceptions.RequestException as e:
        logger.error(f"[LOGIN] Request failed: {str(e)}")
        return False, {"error": str(e)}


def validate_jwt_token(token: str, jwt_secret: str) -> Tuple[bool, Optional[Dict]]:
    """
    Test Step 2: Decode and validate JWT token.
    
    Returns:
        (success, decoded_payload)
    """
    logger.info(f"[JWT] Token length: {len(token)} chars")
    logger.info(f"[JWT] Token prefix: {token[:20]}...")
    
    try:
        # Decode without verification first (to see contents)
        unverified = jwt.decode(token, options={"verify_signature": False})
        logger.info(f"[JWT] Unverified claims: {list(unverified.keys())}")
        
        # Decode with verification
        decoded = jwt.decode(
            token,
            jwt_secret,
            algorithms=["HS256"]
        )
        
        logger.info(f"[JWT] Decoded successfully")
        logger.info(f"[JWT] User ID: {decoded.get('user_id')}")
        logger.info(f"[JWT] Email: {decoded.get('email')}")
        logger.info(f"[JWT] Business ID: {decoded.get('business_id')}")
        
        # Check required claims
        required_claims = ['user_id', 'email', 'exp']
        missing_claims = [claim for claim in required_claims if claim not in decoded]
        
        if missing_claims:
            logger.warning(f"[JWT] Missing claims: {missing_claims}")
        
        return True, decoded
        
    except jwt.ExpiredSignatureError:
        logger.error("[JWT] Token has expired")
        return False, None
    except jwt.InvalidTokenError as e:
        logger.error(f"[JWT] Invalid token: {str(e)}")
        return False, None
    except Exception as e:
        logger.error(f"[JWT] Decode error: {str(e)}")
        return False, None


def test_protected_endpoint(base_url: str, token: str) -> Tuple[bool, Optional[Dict]]:
    """
    Test Step 3: Access protected endpoint with JWT.
    
    Returns:
        (success, response_data)
    """
    # Try to access business endpoint (requires auth)
    business_url = urljoin(base_url, "/api/business/me")
    logger.info(f"[PROTECTED] Calling {business_url}")
    
    try:
        response = requests.get(
            business_url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        logger.info(f"[PROTECTED] HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"[PROTECTED] Response keys: {list(data.keys())}")
            return True, data
        else:
            error_detail = response.text[:200]
            logger.error(f"[PROTECTED] Error: {error_detail}")
            return False, {"error": error_detail, "status": response.status_code}
            
    except requests.exceptions.RequestException as e:
        logger.error(f"[PROTECTED] Request failed: {str(e)}")
        return False, {"error": str(e)}


def verify_authentication(email: str, password: str, base_url: str) -> AuthVerificationResult:
    """
    Run complete authentication verification.
    
    Args:
        email: User email
        password: User password
        base_url: API base URL
        
    Returns:
        AuthVerificationResult with all test results
    """
    result = AuthVerificationResult()
    
    logger.info("="*70)
    logger.info("STARTING AUTHENTICATION VERIFICATION")
    logger.info("="*70)
    logger.info(f"Email: {email}")
    logger.info(f"API URL: {base_url}")
    logger.info(f"Timestamp: {datetime.utcnow().isoformat()}")
    logger.info("="*70)
    
    # Get JWT secret for validation
    settings = get_settings()
    jwt_secret = settings.admin_private_key
    
    if not jwt_secret:
        result.add_step(
            "JWT Secret Check",
            False,
            "ADMIN_PRIVATE_KEY not configured - cannot validate tokens"
        )
        return result
    
    result.add_step(
        "JWT Secret Check",
        True,
        f"JWT secret configured ({len(jwt_secret)} chars)"
    )
    
    # Step 1: Test login endpoint
    login_success, login_data = test_login_endpoint(base_url, email, password)
    
    if not login_success:
        result.add_step(
            "Login Endpoint",
            False,
            f"Login failed: {login_data.get('error', 'Unknown error')}",
            login_data
        )
        return result
    
    result.add_step(
        "Login Endpoint",
        True,
        "Login successful, JWT token received",
        {"status": 200, "has_token": "access_token" in login_data}
    )
    
    # Extract token
    token = login_data.get("access_token")
    if not token:
        result.add_step(
            "Token Extraction",
            False,
            "No access_token in response"
        )
        return result
    
    result.token = token
    result.user_info = login_data.get("user", {})
    
    result.add_step(
        "Token Extraction",
        True,
        f"Token extracted ({len(token)} chars)"
    )
    
    # Step 2: Validate JWT
    jwt_valid, decoded = validate_jwt_token(token, jwt_secret)
    
    if not jwt_valid:
        result.add_step(
            "JWT Validation",
            False,
            "JWT decode/validation failed"
        )
        return result
    
    result.decoded_token = decoded
    result.add_step(
        "JWT Validation",
        True,
        f"JWT valid, claims: user_id={decoded.get('user_id')}, email={decoded.get('email')}",
        decoded
    )
    
    # Step 3: Test protected endpoint
    protected_success, protected_data = test_protected_endpoint(base_url, token)
    
    if not protected_success:
        result.add_step(
            "Protected Endpoint",
            False,
            f"Protected endpoint failed: {protected_data.get('error', 'Unknown')}",
            protected_data
        )
        # This is a warning, not a failure
    else:
        result.add_step(
            "Protected Endpoint",
            True,
            "Successfully accessed protected endpoint with JWT",
            {"business_data": protected_data.keys() if protected_data else []}
        )
    
    return result


def main():
    """Main entry point for login verification."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Verify authentication end-to-end")
    parser.add_argument("email", help="User email address")
    parser.add_argument("password", help="User password")
    parser.add_argument(
        "--url",
        default="https://receptionist.lexmakesit.com",
        help="API base URL (default: https://receptionist.lexmakesit.com)"
    )
    
    args = parser.parse_args()
    
    # Run verification
    result = verify_authentication(args.email, args.password, args.url)
    
    # Print summary
    result.print_summary()
    
    # Exit with appropriate code
    sys.exit(0 if result.is_success() else 1)


if __name__ == "__main__":
    main()
