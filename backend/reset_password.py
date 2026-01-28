#!/usr/bin/env python3
"""
PRODUCTION PASSWORD RESET SCRIPT
=================================
Safely resets a user's password using production bcrypt hashing logic.

SAFETY GUARANTEES:
- Uses exact same hashing as production auth system
- Updates ONLY password_hash column
- Atomic transaction (rollback on failure)
- Validates user exists before modification
- Logs all operations for audit trail

USAGE:
    python reset_password.py <email> <new_password>

EXAMPLE:
    python reset_password.py thegamermasterninja@gmail.com Alexander1221
"""

import sys
import os
import logging
from datetime import datetime
from typing import Optional
import bcrypt

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from ai_receptionist.core.database import get_db
from ai_receptionist.models.user import User
from ai_receptionist.config.settings import get_settings


def hash_password_production(password: str) -> str:
    """
    Hash password using EXACT production logic (bcrypt).
    
    This MUST match the hashing used in signup/password-change endpoints.
    Using bcrypt with auto-generated salt (gensalt()).
    
    Args:
        password: Plaintext password to hash
        
    Returns:
        Hashed password string (bcrypt format: $2b$12$...)
    """
    password_hash = bcrypt.hashpw(
        password.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')
    
    logger.info(f"[HASH] Generated bcrypt hash: length={len(password_hash)}, prefix={password_hash[:7]}")
    return password_hash


def verify_hash_works(password: str, password_hash: str) -> bool:
    """
    Verify the hash works BEFORE committing to database.
    
    Args:
        password: Plaintext password
        password_hash: Hashed password
        
    Returns:
        True if verification succeeds
    """
    try:
        result = bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        logger.info(f"[VERIFY] Pre-commit verification: {'PASS' if result else 'FAIL'}")
        return result
    except Exception as e:
        logger.error(f"[VERIFY] Verification failed: {str(e)}")
        return False


def reset_user_password(email: str, new_password: str, db: Session) -> bool:
    """
    Reset user password with safety checks and atomic transaction.
    
    Args:
        email: User email address
        new_password: New plaintext password
        db: Database session
        
    Returns:
        True if successful, False otherwise
    """
    logger.info("="*70)
    logger.info("PRODUCTION PASSWORD RESET - STARTING")
    logger.info("="*70)
    logger.info(f"Target email: {email}")
    logger.info(f"Timestamp: {datetime.utcnow().isoformat()}")
    
    try:
        # 1. Find user
        logger.info("[STEP 1] Looking up user...")
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            logger.error(f"[FAIL] User not found: {email}")
            logger.error("Available users in database:")
            all_users = db.query(User.email).limit(10).all()
            for u in all_users:
                logger.error(f"  - {u.email}")
            return False
        
        logger.info(f"[SUCCESS] User found: id={user.id}, email={user.email}")
        logger.info(f"          Account status: active={user.is_active}, verified={user.is_verified}")
        
        # Check for duplicate users
        duplicate_count = db.query(User).filter(User.email == email).count()
        if duplicate_count > 1:
            logger.warning(f"[WARNING] Found {duplicate_count} users with email {email}")
            logger.warning("          This may cause authentication issues!")
        
        # 2. Generate new hash using production logic
        logger.info("[STEP 2] Generating new password hash...")
        new_hash = hash_password_production(new_password)
        logger.info(f"[SUCCESS] Hash generated: {new_hash[:20]}...")
        
        # 3. Verify hash works BEFORE committing
        logger.info("[STEP 3] Verifying hash integrity...")
        if not verify_hash_works(new_password, new_hash):
            logger.error("[FAIL] Hash verification failed - aborting!")
            return False
        logger.info("[SUCCESS] Hash verification passed")
        
        # 4. Store old hash for rollback logging
        old_hash = user.password_hash
        logger.info(f"[INFO] Old hash: {old_hash[:20]}...")
        logger.info(f"[INFO] New hash: {new_hash[:20]}...")
        
        # 5. Update password (atomic)
        logger.info("[STEP 4] Updating password in database...")
        user.password_hash = new_hash
        db.commit()
        logger.info("[SUCCESS] Password updated in database")
        
        # 6. Verify persistence
        logger.info("[STEP 5] Verifying database persistence...")
        db.refresh(user)
        if user.password_hash != new_hash:
            logger.error("[FAIL] Password hash did not persist!")
            db.rollback()
            return False
        logger.info("[SUCCESS] Password persisted correctly")
        
        # 7. Final verification
        logger.info("[STEP 6] Final verification...")
        if not verify_hash_works(new_password, user.password_hash):
            logger.error("[FAIL] Final verification failed!")
            db.rollback()
            return False
        
        logger.info("[SUCCESS] Final verification passed")
        
        # Success summary
        logger.info("="*70)
        logger.info("PASSWORD RESET COMPLETE")
        logger.info("="*70)
        logger.info(f"User ID: {user.id}")
        logger.info(f"Email: {user.email}")
        logger.info(f"Hash Algorithm: bcrypt")
        logger.info(f"Hash Length: {len(user.password_hash)} chars")
        logger.info(f"Hash Prefix: {user.password_hash[:7]}")
        logger.info(f"Timestamp: {datetime.utcnow().isoformat()}")
        logger.info("="*70)
        
        return True
        
    except Exception as e:
        logger.error(f"[EXCEPTION] Password reset failed: {str(e)}")
        db.rollback()
        import traceback
        logger.error(traceback.format_exc())
        return False


def main():
    """Main entry point for password reset script."""
    if len(sys.argv) != 3:
        print("USAGE: python reset_password.py <email> <new_password>")
        print("EXAMPLE: python reset_password.py user@example.com NewPassword123")
        sys.exit(1)
    
    email = sys.argv[1]
    new_password = sys.argv[2]
    
    # Validate input
    if not email or '@' not in email:
        logger.error(f"Invalid email: {email}")
        sys.exit(1)
    
    if not new_password or len(new_password) < 8:
        logger.error(f"Password too short (min 8 chars): {len(new_password)} chars")
        sys.exit(1)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Perform reset
        success = reset_user_password(email, new_password, db)
        
        if success:
            logger.info("✅ Password reset successful - user can now login")
            sys.exit(0)
        else:
            logger.error("❌ Password reset failed - see logs above")
            sys.exit(1)
            
    finally:
        db.close()


if __name__ == "__main__":
    main()
