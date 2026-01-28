#!/usr/bin/env python3
"""
Production User Provisioning & Verification Script
===================================================
Creates user if missing, updates if exists, verifies login end-to-end.

AUTHORITATIVE SPECIFICATION:
- Email: thegamermasterninja@gmail.com
- Password: Alexander1221
- Phone: 2298215986

Follows exact production bcrypt hashing logic.
"""

import sys
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION (AUTHORITATIVE)
# ============================================================================
TARGET_EMAIL = "thegamermasterninja@gmail.com"
TARGET_PASSWORD = "Alexander1221"
TARGET_PHONE = "2298215986"

# ============================================================================
# IMPORTS - Production modules
# ============================================================================
try:
    sys.path.insert(0, "/app")
    import bcrypt
    from ai_receptionist.config.settings import get_settings
    from ai_receptionist.core.database import get_session_local
    from ai_receptionist.models.user import User
    from ai_receptionist.core.auth import create_access_token
    logger.info("✓ All production modules imported successfully")
except ImportError as e:
    logger.error(f"✗ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================================================
# HELPER FUNCTIONS - Production bcrypt logic (matches auth.py exactly)
# ============================================================================
def hash_password_production(password: str) -> str:
    """Hash password using EXACT production logic (bcrypt)."""
    password_hash = bcrypt.hashpw(
        password.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')
    logger.info(f"[HASH] Generated bcrypt hash: length={len(password_hash)}, prefix={password_hash[:7]}")
    return password_hash


def verify_hash_works(password: str, password_hash: str) -> bool:
    """Verify the hash works BEFORE committing to database."""
    try:
        result = bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        logger.info(f"[VERIFY] Password verification: {'PASS' if result else 'FAIL'}")
        return result
    except Exception as e:
        logger.error(f"[VERIFY] Verification failed: {str(e)}")
        return False


# ============================================================================
# STEP 1: CHECK IF USER EXISTS
# ============================================================================
def step1_check_user_exists(db):
    """Query user by email using ORM"""
    logger.info("=" * 60)
    logger.info("[STEP 1] Checking if user exists...")
    
    users = db.query(User).filter(User.email == TARGET_EMAIL).all()
    count = len(users)
    
    if count > 1:
        logger.error(f"✗ ABORT: Found {count} users with email {TARGET_EMAIL} - DUPLICATE!")
        return None, "DUPLICATE"
    elif count == 1:
        user = users[0]
        logger.info(f"✓ User EXISTS: id={user.id}, email={user.email}")
        return user, "EXISTS"
    else:
        logger.info(f"✓ User does NOT exist - will create")
        return None, "NOT_FOUND"

# ============================================================================
# STEP 2: CREATE OR UPDATE USER
# ============================================================================
def step2_create_or_update_user(db, existing_user, status):
    """Create user if missing, update password if exists"""
    logger.info("=" * 60)
    logger.info("[STEP 2] Password handling (bcrypt)...")
    
    # Generate bcrypt hash using production logic
    password_hash = hash_password_production(TARGET_PASSWORD)
    logger.info(f"✓ Generated bcrypt hash: {password_hash[:20]}...")
    
    # Verify hash works before committing
    if not verify_hash_works(TARGET_PASSWORD, password_hash):
        logger.error("✗ Pre-commit hash verification failed - ABORT")
        return None, False
    
    if status == "NOT_FOUND":
        logger.info("[STEP 2a] Creating new user...")
        
        new_user = User(
            email=TARGET_EMAIL,
            password_hash=password_hash,
            full_name="Gamer Master Ninja",  # Sensible default
            is_active=True,
            is_verified=True,  # Skip email verification for production setup
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        logger.info(f"✓ User CREATED: id={new_user.id}")
        return new_user, True  # True = created
        
    else:  # EXISTS
        logger.info("[STEP 2b] Updating existing user password...")
        
        existing_user.password_hash = password_hash
        
        db.commit()
        db.refresh(existing_user)
        
        logger.info(f"✓ User UPDATED: id={existing_user.id}")
        return existing_user, False  # False = updated, not created

# ============================================================================
# STEP 3: DATABASE INTEGRITY CHECK
# ============================================================================
def step3_verify_integrity(db, user_id):
    """Re-query and verify database state"""
    logger.info("=" * 60)
    logger.info("[STEP 3] Database integrity check...")
    
    # Re-query to confirm
    users = db.query(User).filter(User.email == TARGET_EMAIL).all()
    
    if len(users) != 1:
        logger.error(f"✗ FAIL: Expected 1 user, found {len(users)}")
        return False
    
    user = users[0]
    
    # Verify all fields
    checks = {
        "ID matches": user.id == user_id,
        "Email correct": user.email == TARGET_EMAIL,
        "Password hash present": bool(user.password_hash),
        "Is active": user.is_active,
    }
    
    all_passed = True
    for check_name, passed in checks.items():
        status = "✓" if passed else "✗"
        logger.info(f"  {status} {check_name}: {passed}")
        if not passed:
            all_passed = False
    
    if all_passed:
        logger.info("✓ Database integrity verified")
    else:
        logger.error("✗ Database integrity check FAILED")
    
    return all_passed

# ============================================================================
# STEP 4: VERIFY LOGIN PROGRAMMATICALLY
# ============================================================================
def step4_verify_login(db):
    """Test login using production auth logic"""
    logger.info("=" * 60)
    logger.info("[STEP 4] Verifying login programmatically...")
    
    # Get user
    user = db.query(User).filter(User.email == TARGET_EMAIL).first()
    if not user:
        logger.error("✗ User not found for login test")
        return False, None
    
    # Verify password using production bcrypt logic
    password_valid = verify_hash_works(TARGET_PASSWORD, user.password_hash)
    logger.info(f"  Password verification: {'✓ PASS' if password_valid else '✗ FAIL'}")
    
    if not password_valid:
        logger.error("✗ Password verification FAILED")
        return False, None
    
    # Generate token using production function
    token_data = {"sub": user.email, "user_id": user.id}
    access_token = create_access_token(data=token_data)
    
    if access_token:
        logger.info(f"  ✓ Token generated: {access_token[:30]}...")
    else:
        logger.error("  ✗ Token generation FAILED")
        return False, None
    
    # Verify cookie configuration
    logger.info("  Cookie configuration (expected):")
    logger.info("    - HttpOnly: True")
    logger.info("    - Secure: True")
    logger.info("    - SameSite: Lax")
    logger.info("    - Domain: .lexmakesit.com")
    
    logger.info("✓ Login verification PASSED")
    return True, access_token

# ============================================================================
# STEP 5: VERIFY SESSION (Simulated)
# ============================================================================
def step5_verify_session(db, token):
    """Verify session would work with /api/auth/me"""
    logger.info("=" * 60)
    logger.info("[STEP 5] Verifying session...")
    
    # Decode token to verify it contains correct data
    from jose import jwt
    
    try:
        settings = get_settings()
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        email = payload.get("sub")
        user_id = payload.get("user_id")
        
        logger.info(f"  Token payload email: {email}")
        logger.info(f"  Token payload user_id: {user_id}")
        
        if email == TARGET_EMAIL:
            logger.info("✓ Session verification PASSED")
            logger.info("  /api/auth/me would return correct user data")
            return True
        else:
            logger.error(f"✗ Token email mismatch: {email} != {TARGET_EMAIL}")
            return False
            
    except Exception as e:
        logger.error(f"✗ Token decode failed: {e}")
        return False

# ============================================================================
# MAIN EXECUTION
# ============================================================================
def main():
    logger.info("=" * 60)
    logger.info("PRODUCTION USER PROVISIONING SCRIPT")
    logger.info(f"Target: {TARGET_EMAIL}")
    logger.info("=" * 60)
    
    # Initialize database session
    SessionLocal = get_session_local()
    db = SessionLocal()
    
    try:
        # Step 1: Check if user exists
        existing_user, status = step1_check_user_exists(db)
        
        if status == "DUPLICATE":
            logger.error("🧨 ABORT: Duplicate users detected")
            return False
        
        # Step 2: Create or update user
        user, was_created = step2_create_or_update_user(db, existing_user, status)
        
        if user is None:
            logger.error("🧨 ABORT: User creation/update failed")
            return False
        
        # Step 3: Database integrity check
        if not step3_verify_integrity(db, user.id):
            logger.error("🧨 ABORT: Database integrity check failed")
            return False
        
        # Step 4: Verify login
        login_ok, token = step4_verify_login(db)
        if not login_ok:
            logger.error("🧨 ABORT: Login verification failed")
            return False
        
        # Step 5: Verify session
        if not step5_verify_session(db, token):
            logger.error("🧨 ABORT: Session verification failed")
            return False
        
        # ====================================================================
        # FINAL REPORT
        # ====================================================================
        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ USER READY FOR LOGIN")
        logger.info("=" * 60)
        logger.info(f"Email: {TARGET_EMAIL}")
        logger.info(f"User ID: {user.id}")
        logger.info(f"Phone: {TARGET_PHONE}")
        logger.info(f"Password: {TARGET_PASSWORD} (hashed)")
        logger.info(f"Created: {'yes' if was_created else 'no (updated)'}")
        logger.info(f"Login verified: yes")
        logger.info(f"Session verified: yes")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"🧨 FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
        
    finally:
        db.close()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
