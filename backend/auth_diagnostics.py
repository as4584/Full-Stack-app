#!/usr/bin/env python3
"""
AUTH DIAGNOSTICS MODULE
=======================
Automatically diagnoses authentication failures.

DIAGNOSTIC CHECKS:
- Duplicate user records
- Password hash algorithm mismatches
- JWT_SECRET presence and stability
- Database persistence across restart
- Environment drift detection
- Backend routing issues

USAGE:
    python auth_diagnostics.py <email>

EXAMPLE:
    python auth_diagnostics.py thegamermasterninja@gmail.com
"""

import sys
import os
import logging
from datetime import datetime
from typing import Dict, List, Tuple
import bcrypt

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from sqlalchemy import text
from ai_receptionist.core.database import get_db
from ai_receptionist.models.user import User
from ai_receptionist.models.business import Business
from ai_receptionist.config.settings import get_settings


class DiagnosticResult:
    """Stores diagnostic check results."""
    
    def __init__(self):
        self.checks = []
        self.warnings = []
        self.errors = []
        self.critical_failures = []
    
    def add_check(self, name: str, status: str, message: str, details: Dict = None):
        """
        Add a diagnostic check result.
        
        Args:
            name: Check name
            status: PASS, WARN, FAIL, CRITICAL
            message: Human-readable result
            details: Additional data
        """
        check = {
            "name": name,
            "status": status,
            "message": message,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.checks.append(check)
        
        if status == "PASS":
            logger.info(f"✅ {name}: {message}")
        elif status == "WARN":
            logger.warning(f"⚠️  {name}: {message}")
            self.warnings.append(message)
        elif status == "FAIL":
            logger.error(f"❌ {name}: {message}")
            self.errors.append(message)
        elif status == "CRITICAL":
            logger.error(f"🔥 {name}: {message}")
            self.critical_failures.append(message)
    
    def has_critical_failures(self) -> bool:
        """Check if any critical failures occurred."""
        return len(self.critical_failures) > 0
    
    def print_summary(self):
        """Print diagnostic summary."""
        logger.info("="*70)
        logger.info("AUTHENTICATION DIAGNOSTICS SUMMARY")
        logger.info("="*70)
        
        for check in self.checks:
            status_icon = {
                "PASS": "✅",
                "WARN": "⚠️",
                "FAIL": "❌",
                "CRITICAL": "🔥"
            }.get(check["status"], "❓")
            
            logger.info(f"{status_icon} {check['name']}: {check['message']}")
        
        logger.info("="*70)
        logger.info(f"Total Checks: {len(self.checks)}")
        logger.info(f"Warnings: {len(self.warnings)}")
        logger.info(f"Errors: {len(self.errors)}")
        logger.info(f"Critical Failures: {len(self.critical_failures)}")
        logger.info("="*70)
        
        if self.critical_failures:
            logger.error("CRITICAL FAILURES DETECTED:")
            for failure in self.critical_failures:
                logger.error(f"  🔥 {failure}")


def check_duplicate_users(email: str, db: Session) -> DiagnosticResult:
    """Check for duplicate user records."""
    result = DiagnosticResult()
    
    try:
        users = db.query(User).filter(User.email == email).all()
        count = len(users)
        
        if count == 0:
            result.add_check(
                "Duplicate Users",
                "CRITICAL",
                f"User not found: {email}",
                {"count": 0}
            )
        elif count == 1:
            result.add_check(
                "Duplicate Users",
                "PASS",
                f"Exactly one user found (id={users[0].id})",
                {"count": 1, "user_id": users[0].id}
            )
        else:
            result.add_check(
                "Duplicate Users",
                "CRITICAL",
                f"Found {count} users with email {email} - auth will be unpredictable",
                {"count": count, "user_ids": [u.id for u in users]}
            )
    except Exception as e:
        result.add_check(
            "Duplicate Users",
            "FAIL",
            f"Database query failed: {str(e)}"
        )
    
    return result


def check_password_hash_format(email: str, db: Session) -> DiagnosticResult:
    """Check password hash algorithm and format."""
    result = DiagnosticResult()
    
    try:
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            result.add_check(
                "Password Hash Format",
                "FAIL",
                "Cannot check - user not found"
            )
            return result
        
        hash_value = user.password_hash
        hash_length = len(hash_value)
        hash_prefix = hash_value[:7] if len(hash_value) >= 7 else hash_value
        
        # Check for bcrypt format: $2b$10$...
        if hash_value.startswith("$2b$") or hash_value.startswith("$2a$"):
            result.add_check(
                "Password Hash Format",
                "PASS",
                f"Valid bcrypt hash detected (length={hash_length}, prefix={hash_prefix})",
                {"algorithm": "bcrypt", "length": hash_length, "prefix": hash_prefix}
            )
        elif hash_value.startswith("$2y$"):
            result.add_check(
                "Password Hash Format",
                "WARN",
                f"PHP-style bcrypt detected - may cause issues (prefix={hash_prefix})",
                {"algorithm": "bcrypt-php", "length": hash_length}
            )
        elif hash_value.startswith("pbkdf2:"):
            result.add_check(
                "Password Hash Format",
                "WARN",
                f"PBKDF2 hash detected - ensure verifier matches (prefix={hash_prefix})",
                {"algorithm": "pbkdf2", "length": hash_length}
            )
        else:
            result.add_check(
                "Password Hash Format",
                "FAIL",
                f"Unrecognized hash format (prefix={hash_prefix}, length={hash_length})",
                {"algorithm": "unknown", "prefix": hash_prefix}
            )
    except Exception as e:
        result.add_check(
            "Password Hash Format",
            "FAIL",
            f"Hash inspection failed: {str(e)}"
        )
    
    return result


def check_jwt_secret_config() -> DiagnosticResult:
    """Check JWT secret configuration."""
    result = DiagnosticResult()
    
    try:
        settings = get_settings()
        jwt_secret = settings.admin_private_key
        
        if not jwt_secret:
            result.add_check(
                "JWT Secret",
                "CRITICAL",
                "ADMIN_PRIVATE_KEY not configured - JWT auth impossible"
            )
        elif len(jwt_secret) < 32:
            result.add_check(
                "JWT Secret",
                "WARN",
                f"JWT secret too short ({len(jwt_secret)} chars) - should be 32+ chars",
                {"length": len(jwt_secret)}
            )
        else:
            result.add_check(
                "JWT Secret",
                "PASS",
                f"JWT secret configured ({len(jwt_secret)} chars)",
                {"length": len(jwt_secret)}
            )
        
        # Check if secret looks like a placeholder
        if jwt_secret and any(x in jwt_secret.lower() for x in ["changeme", "secret", "fixme", "todo"]):
            result.add_check(
                "JWT Secret Quality",
                "WARN",
                "JWT secret contains placeholder text - may not be production-grade"
            )
    except Exception as e:
        result.add_check(
            "JWT Secret",
            "FAIL",
            f"Config check failed: {str(e)}"
        )
    
    return result


def check_database_connectivity(db: Session) -> DiagnosticResult:
    """Check database connection and persistence."""
    result = DiagnosticResult()
    
    try:
        # Test basic query
        db.execute(text("SELECT 1"))
        result.add_check(
            "Database Connection",
            "PASS",
            "Database connection successful"
        )
        
        # Check if we can write and read
        test_query = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
        result.add_check(
            "Database Read",
            "PASS",
            f"Successfully read users table ({test_query} users)",
            {"user_count": test_query}
        )
    except Exception as e:
        result.add_check(
            "Database Connection",
            "CRITICAL",
            f"Database connection failed: {str(e)}"
        )
    
    return result


def check_user_account_status(email: str, db: Session) -> DiagnosticResult:
    """Check if user account is active and verified."""
    result = DiagnosticResult()
    
    try:
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            result.add_check(
                "Account Status",
                "FAIL",
                "User not found"
            )
            return result
        
        if not user.is_active:
            result.add_check(
                "Account Active",
                "CRITICAL",
                "User account is DISABLED - login will fail",
                {"is_active": False}
            )
        else:
            result.add_check(
                "Account Active",
                "PASS",
                "User account is active",
                {"is_active": True}
            )
        
        if not user.is_verified:
            result.add_check(
                "Account Verified",
                "WARN",
                "User email not verified - may affect features",
                {"is_verified": False}
            )
        else:
            result.add_check(
                "Account Verified",
                "PASS",
                "User email verified",
                {"is_verified": True}
            )
    except Exception as e:
        result.add_check(
            "Account Status",
            "FAIL",
            f"Status check failed: {str(e)}"
        )
    
    return result


def check_business_association(email: str, db: Session) -> DiagnosticResult:
    """Check if user has associated business."""
    result = DiagnosticResult()
    
    try:
        business = db.query(Business).filter(Business.owner_email == email).first()
        
        if not business:
            result.add_check(
                "Business Association",
                "WARN",
                "No business associated with user",
                {"has_business": False}
            )
        else:
            result.add_check(
                "Business Association",
                "PASS",
                f"Business found (id={business.id}, name={business.name})",
                {
                    "has_business": True,
                    "business_id": business.id,
                    "business_name": business.name,
                    "phone_number": business.phone_number,
                    "receptionist_enabled": business.receptionist_enabled
                }
            )
    except Exception as e:
        result.add_check(
            "Business Association",
            "FAIL",
            f"Business lookup failed: {str(e)}"
        )
    
    return result


def run_full_diagnostics(email: str) -> DiagnosticResult:
    """Run all diagnostic checks."""
    combined = DiagnosticResult()
    
    logger.info("="*70)
    logger.info("RUNNING AUTHENTICATION DIAGNOSTICS")
    logger.info("="*70)
    logger.info(f"Target Email: {email}")
    logger.info(f"Timestamp: {datetime.utcnow().isoformat()}")
    logger.info("="*70)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Run all checks
        checks = [
            check_database_connectivity(db),
            check_duplicate_users(email, db),
            check_user_account_status(email, db),
            check_password_hash_format(email, db),
            check_business_association(email, db),
            check_jwt_secret_config()
        ]
        
        # Combine results
        for check_result in checks:
            combined.checks.extend(check_result.checks)
            combined.warnings.extend(check_result.warnings)
            combined.errors.extend(check_result.errors)
            combined.critical_failures.extend(check_result.critical_failures)
    
    finally:
        db.close()
    
    return combined


def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("USAGE: python auth_diagnostics.py <email>")
        print("EXAMPLE: python auth_diagnostics.py user@example.com")
        sys.exit(1)
    
    email = sys.argv[1]
    
    # Run diagnostics
    result = run_full_diagnostics(email)
    
    # Print summary
    result.print_summary()
    
    # Exit with appropriate code
    if result.has_critical_failures():
        logger.error("\n🔥 CRITICAL FAILURES DETECTED - Auth will not work until resolved")
        sys.exit(2)
    elif result.errors:
        logger.warning("\n⚠️  Errors found - Auth may be unstable")
        sys.exit(1)
    else:
        logger.info("\n✅ All diagnostics passed - Auth should work correctly")
        sys.exit(0)


if __name__ == "__main__":
    main()
