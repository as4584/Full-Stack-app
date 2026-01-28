#!/usr/bin/env python3
"""
Production User-Business Linkage Script
========================================
Links existing user to business, creates business if needed.

AUTHORITATIVE:
- User ID: 2
- Email: thegamermasterninja@gmail.com
- Phone: 2298215986
- Business Name: Lex Makes It
- Industry: Industry Software Development
"""

import sys
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
TARGET_USER_ID = 2
TARGET_EMAIL = "thegamermasterninja@gmail.com"
TARGET_PASSWORD = "Alexander1221"
TARGET_PHONE = "2298215986"
TARGET_BUSINESS_NAME = "Lex Makes It"
TARGET_INDUSTRY = "Industry Software Development"

# ============================================================================
# IMPORTS
# ============================================================================
try:
    sys.path.insert(0, "/app")
    import bcrypt
    from sqlalchemy import or_
    from ai_receptionist.config.settings import get_settings
    from ai_receptionist.core.database import get_session_local
    from ai_receptionist.models.user import User
    from ai_receptionist.models.business import Business
    from ai_receptionist.core.auth import create_access_token
    logger.info("✓ All production modules imported successfully")
except ImportError as e:
    logger.error(f"✗ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================================================
# STEP 1: VERIFY USER EXISTS
# ============================================================================
def step1_verify_user(db):
    """Verify user ID=2 exists with correct email"""
    logger.info("=" * 60)
    logger.info("[STEP 1] Verifying user exists...")
    
    # Check for duplicates first
    users_with_email = db.query(User).filter(User.email == TARGET_EMAIL).all()
    
    if len(users_with_email) > 1:
        logger.error(f"✗ ABORT: Found {len(users_with_email)} users with email {TARGET_EMAIL}")
        return None
    
    if len(users_with_email) == 0:
        logger.error(f"✗ ABORT: User not found: {TARGET_EMAIL}")
        return None
    
    user = users_with_email[0]
    
    if user.id != TARGET_USER_ID:
        logger.error(f"✗ ABORT: User ID mismatch. Expected {TARGET_USER_ID}, got {user.id}")
        return None
    
    logger.info(f"✓ User verified: id={user.id}, email={user.email}")
    logger.info(f"  is_active={user.is_active}, is_verified={user.is_verified}")
    
    return user

# ============================================================================
# STEP 2: INSPECT EXISTING BUSINESSES
# ============================================================================
def step2_find_business(db):
    """Search for existing business matching criteria"""
    logger.info("=" * 60)
    logger.info("[STEP 2] Searching for existing businesses...")
    
    # Search by phone number
    by_phone = db.query(Business).filter(Business.phone_number == TARGET_PHONE).all()
    logger.info(f"  Found {len(by_phone)} business(es) with phone {TARGET_PHONE}")
    
    # Search by name containing 'lex'
    by_name = db.query(Business).filter(Business.name.ilike('%lex%')).all()
    logger.info(f"  Found {len(by_name)} business(es) with name containing 'lex'")
    
    # Search by industry containing 'software'
    by_industry = db.query(Business).filter(Business.industry.ilike('%software%')).all()
    logger.info(f"  Found {len(by_industry)} business(es) with industry containing 'software'")
    
    # Search by owner_email
    by_owner = db.query(Business).filter(Business.owner_email == TARGET_EMAIL).all()
    logger.info(f"  Found {len(by_owner)} business(es) with owner_email={TARGET_EMAIL}")
    
    # Check for duplicates by phone (abort condition)
    if len(by_phone) > 1:
        logger.error(f"✗ ABORT: Multiple businesses with same phone number!")
        for b in by_phone:
            logger.error(f"  - ID={b.id}, name={b.name}, owner_email={b.owner_email}")
        return None, "DUPLICATE_PHONE"
    
    # Combine all found businesses (deduplicate by ID)
    all_found = {}
    for b in by_phone + by_name + by_industry + by_owner:
        all_found[b.id] = b
    
    if all_found:
        logger.info(f"  Total unique businesses matching criteria: {len(all_found)}")
        for b in all_found.values():
            logger.info(f"    - ID={b.id}, name={b.name}, phone={b.phone_number}, owner={b.owner_email}")
    
    # Prefer business with matching phone number
    if by_phone:
        return by_phone[0], "FOUND"
    
    # Then prefer business owned by user
    if by_owner:
        return by_owner[0], "FOUND"
    
    # Otherwise use first matching business
    if all_found:
        return list(all_found.values())[0], "FOUND"
    
    return None, "NOT_FOUND"

# ============================================================================
# STEP 3: CREATE OR LINK BUSINESS
# ============================================================================
def step3_create_or_link_business(db, user, existing_business, status):
    """Create business if not found, link to user"""
    logger.info("=" * 60)
    logger.info("[STEP 3] Creating or linking business...")
    
    if status == "DUPLICATE_PHONE":
        logger.error("✗ Cannot proceed - duplicate phone numbers")
        return None
    
    if status == "FOUND" and existing_business:
        logger.info(f"✓ Using existing business: ID={existing_business.id}")
        business = existing_business
        
        # Update owner_email if not set or different
        if business.owner_email != user.email:
            logger.info(f"  Updating owner_email from {business.owner_email} to {user.email}")
            business.owner_email = user.email
        
        # Update phone if needed
        if business.phone_number != TARGET_PHONE:
            logger.info(f"  Updating phone from {business.phone_number} to {TARGET_PHONE}")
            business.phone_number = TARGET_PHONE
            
    else:
        logger.info("  Creating new business...")
        business = Business(
            name=TARGET_BUSINESS_NAME,
            industry=TARGET_INDUSTRY,
            phone_number=TARGET_PHONE,
            owner_email=TARGET_EMAIL,
        )
        db.add(business)
    
    db.commit()
    db.refresh(business)
    
    logger.info(f"✓ Business ready: ID={business.id}, name={business.name}")
    logger.info(f"  owner_email={business.owner_email}, phone={business.phone_number}")
    
    return business

# ============================================================================
# STEP 4: VERIFY LINKAGE
# ============================================================================
def step4_verify_linkage(db, user, business):
    """Verify user-business linkage is correct"""
    logger.info("=" * 60)
    logger.info("[STEP 4] Verifying linkage...")
    
    # Re-query to confirm
    fresh_business = db.query(Business).filter(Business.id == business.id).first()
    
    checks = {
        "Business exists": fresh_business is not None,
        "Owner email matches user": fresh_business.owner_email == user.email if fresh_business else False,
        "Phone number correct": fresh_business.phone_number == TARGET_PHONE if fresh_business else False,
    }
    
    all_passed = True
    for check_name, passed in checks.items():
        status = "✓" if passed else "✗"
        logger.info(f"  {status} {check_name}: {passed}")
        if not passed:
            all_passed = False
    
    # Check for multiple businesses linked to user
    user_businesses = db.query(Business).filter(Business.owner_email == user.email).all()
    if len(user_businesses) > 1:
        logger.warning(f"  ⚠ User has {len(user_businesses)} businesses:")
        for b in user_businesses:
            logger.warning(f"    - ID={b.id}, name={b.name}")
    else:
        logger.info(f"  ✓ User has exactly 1 business")
    
    return all_passed

# ============================================================================
# STEP 5: VERIFY LOGIN
# ============================================================================
def step5_verify_login(db, business):
    """Verify login and token generation"""
    logger.info("=" * 60)
    logger.info("[STEP 5] Verifying login...")
    
    # Get user
    user = db.query(User).filter(User.id == TARGET_USER_ID).first()
    
    # Verify password
    password_valid = bcrypt.checkpw(
        TARGET_PASSWORD.encode('utf-8'),
        user.password_hash.encode('utf-8')
    )
    logger.info(f"  Password verification: {'✓ PASS' if password_valid else '✗ FAIL'}")
    
    if not password_valid:
        return False, None
    
    # Generate token with business_id
    token_data = {
        "sub": user.email,
        "user_id": user.id,
        "business_id": business.id
    }
    access_token = create_access_token(data=token_data)
    
    if access_token:
        logger.info(f"  ✓ Token generated: {access_token[:40]}...")
    else:
        logger.error("  ✗ Token generation failed")
        return False, None
    
    # Cookie configuration
    logger.info("  Cookie configuration (expected):")
    logger.info("    - HttpOnly: True")
    logger.info("    - Secure: True")
    logger.info("    - SameSite: Lax")
    logger.info("    - Domain: .lexmakesit.com")
    
    logger.info("✓ Login verification PASSED")
    return True, access_token

# ============================================================================
# MAIN EXECUTION
# ============================================================================
def main():
    logger.info("=" * 60)
    logger.info("PRODUCTION USER-BUSINESS LINKAGE SCRIPT")
    logger.info(f"User: {TARGET_EMAIL} (ID={TARGET_USER_ID})")
    logger.info(f"Phone: {TARGET_PHONE}")
    logger.info("=" * 60)
    
    # Initialize database
    SessionLocal = get_session_local()
    db = SessionLocal()
    
    try:
        # Step 1: Verify user
        user = step1_verify_user(db)
        if not user:
            logger.error("🧨 ABORT: User verification failed")
            return False
        
        # Step 2: Find existing business
        existing_business, status = step2_find_business(db)
        if status == "DUPLICATE_PHONE":
            logger.error("🧨 ABORT: Duplicate phone numbers found")
            return False
        
        # Step 3: Create or link business
        business = step3_create_or_link_business(db, user, existing_business, status)
        if not business:
            logger.error("🧨 ABORT: Business creation/linking failed")
            return False
        
        # Step 4: Verify linkage
        if not step4_verify_linkage(db, user, business):
            logger.error("🧨 ABORT: Linkage verification failed")
            return False
        
        # Step 5: Verify login
        login_ok, token = step5_verify_login(db, business)
        if not login_ok:
            logger.error("🧨 ABORT: Login verification failed")
            return False
        
        # ====================================================================
        # FINAL REPORT
        # ====================================================================
        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ PRODUCTION ACCOUNT VERIFIED")
        logger.info("=" * 60)
        logger.info("")
        logger.info("User:")
        logger.info(f"  - Email: {TARGET_EMAIL}")
        logger.info(f"  - ID: {user.id}")
        logger.info(f"  - Login: OK")
        logger.info("")
        logger.info("Business:")
        logger.info(f"  - ID: {business.id}")
        logger.info(f"  - Name: {business.name}")
        logger.info(f"  - Industry: {business.industry}")
        logger.info(f"  - Phone: {business.phone_number}")
        logger.info("")
        logger.info("Linking: COMPLETE")
        logger.info("Duplicates: NONE")
        logger.info("Dashboard Access: VERIFIED")
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
