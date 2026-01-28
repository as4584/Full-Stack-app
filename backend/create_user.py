#!/usr/bin/env python3
"""
Production-Safe User Creation Script

This script creates a new user in the production database with proper
password hashing using bcrypt. Use this script ONLY when the user does
not exist. For password resets, use reset_password.py instead.

Usage:
    python create_user.py <email> <password> [--full-name "Full Name"]

Example:
    python create_user.py thegamermasterninja@gmail.com Alexander1221 --full-name "Alexander User"

Safety Features:
- Checks for existing user before creation
- Uses production bcrypt hashing with gensalt()
- Pre-verifies hash works before database commit
- Atomic transaction with rollback on failure
- Comprehensive logging for audit trail
"""

import sys
import logging
from datetime import datetime
from typing import Optional
import bcrypt
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Import application modules
try:
    from ai_receptionist.config.settings import get_settings
    from ai_receptionist.core.database import get_engine, get_session_local
    from ai_receptionist.models.user import User
    from sqlalchemy.orm import sessionmaker
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    logger.error("Make sure PYTHONPATH is set correctly: export PYTHONPATH=/app")
    sys.exit(2)


def hash_password_production(password: str) -> str:
    """
    Hash password using production bcrypt settings.
    
    This uses the EXACT same logic as the signup endpoint:
    - bcrypt.gensalt() for salt generation
    - bcrypt.hashpw() for hashing
    - UTF-8 encoding
    - Decode to string for database storage
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string (bcrypt format: $2b$...)
    """
    logger.info("[HASH] Generating bcrypt hash with production settings")
    salt = bcrypt.gensalt()
    password_bytes = password.encode('utf-8')
    hashed_bytes = bcrypt.hashpw(password_bytes, salt)
    hashed_string = hashed_bytes.decode('utf-8')
    
    logger.info(f"[HASH] Hash format: {hashed_string[:20]}...")
    logger.info(f"[HASH] Hash length: {len(hashed_string)} characters")
    
    return hashed_string


def verify_hash_works(password: str, password_hash: str) -> bool:
    """
    Verify the hash can be used to authenticate the password.
    
    This is a critical safety check - we verify the hash works
    BEFORE committing to the database. This prevents creating
    a user with a broken hash.
    
    Args:
        password: Plain text password
        password_hash: Hashed password to verify
        
    Returns:
        True if verification succeeds, False otherwise
    """
    logger.info("[VERIFY] Testing hash before database commit...")
    try:
        password_bytes = password.encode('utf-8')
        hash_bytes = password_hash.encode('utf-8')
        result = bcrypt.checkpw(password_bytes, hash_bytes)
        
        if result:
            logger.info("[VERIFY] ✅ Pre-commit verification PASSED - hash is valid")
        else:
            logger.error("[VERIFY] ❌ Pre-commit verification FAILED - hash is invalid")
            
        return result
    except Exception as e:
        logger.error(f"[VERIFY] ❌ Verification error: {e}")
        return False


def create_user(
    email: str, 
    password: str, 
    full_name: Optional[str],
    db: Session
) -> bool:
    """
    Create a new user with proper password hashing.
    
    Safety checks:
    1. Check if user already exists
    2. Hash password using production bcrypt
    3. Verify hash works before database commit
    4. Atomic transaction with rollback on failure
    
    Args:
        email: User email address (must be unique)
        password: Plain text password
        full_name: User's full name (optional)
        db: Database session
        
    Returns:
        True if user created successfully, False otherwise
    """
    logger.info("=" * 70)
    logger.info("PRODUCTION USER CREATION - STARTING")
    logger.info("=" * 70)
    logger.info(f"Email: {email}")
    logger.info(f"Full name: {full_name or 'Not provided'}")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    
    try:
        # Step 1: Check if user already exists
        logger.info("[STEP 1] Checking if user already exists...")
        existing_user = db.query(User).filter(User.email == email).first()
        
        if existing_user:
            logger.error(f"[FAIL] User already exists: {email}")
            logger.error(f"[FAIL] User ID: {existing_user.id}")
            logger.error(f"[FAIL] Active: {existing_user.is_active}")
            logger.error(f"[FAIL] Verified: {existing_user.is_verified}")
            logger.error("")
            logger.error("💡 To reset password for existing user, use:")
            logger.error(f"   python reset_password.py {email} <new_password>")
            return False
            
        logger.info("[STEP 1] ✅ User does not exist - safe to create")
        
        # Step 2: Hash the password
        logger.info("[STEP 2] Hashing password...")
        password_hash = hash_password_production(password)
        logger.info("[STEP 2] ✅ Password hashed successfully")
        
        # Step 3: Verify hash works
        logger.info("[STEP 3] Verifying hash before commit...")
        if not verify_hash_works(password, password_hash):
            logger.error("[STEP 3] ❌ Hash verification failed - ABORTING")
            logger.error("This is a critical error - hash doesn't work!")
            return False
        logger.info("[STEP 3] ✅ Hash verified successfully")
        
        # Step 4: Create user object
        logger.info("[STEP 4] Creating user object...")
        new_user = User(
            email=email,
            password_hash=password_hash,
            full_name=full_name or email.split('@')[0],
            is_active=True,
            is_verified=True  # Auto-verify for admin-created users
        )
        
        # Step 5: Commit to database
        logger.info("[STEP 5] Committing to database...")
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        logger.info("[STEP 5] ✅ Database commit successful")
        logger.info(f"[STEP 5] New user ID: {new_user.id}")
        
        # Step 6: Final verification
        logger.info("[STEP 6] Running final verification...")
        test_user = db.query(User).filter(User.email == email).first()
        
        if not test_user:
            logger.error("[STEP 6] ❌ User not found after commit!")
            return False
            
        if not bcrypt.checkpw(password.encode('utf-8'), test_user.password_hash.encode('utf-8')):
            logger.error("[STEP 6] ❌ Final verification failed!")
            logger.error("Password hash in database doesn't work!")
            return False
            
        logger.info("[STEP 6] ✅ Final verification passed")
        logger.info("")
        logger.info("=" * 70)
        logger.info("✅ USER CREATION SUCCESSFUL")
        logger.info("=" * 70)
        logger.info(f"Email: {email}")
        logger.info(f"User ID: {test_user.id}")
        logger.info(f"Active: {test_user.is_active}")
        logger.info(f"Verified: {test_user.is_verified}")
        logger.info("")
        logger.info("✅ User can now login with the provided password")
        
        return True
        
    except IntegrityError as e:
        logger.error(f"[FAIL] Database integrity error: {e}")
        logger.error("This usually means the email already exists")
        db.rollback()
        return False
        
    except Exception as e:
        logger.error(f"[FAIL] Unexpected error: {e}")
        logger.error("Rolling back transaction...")
        db.rollback()
        return False


def main():
    """Main entry point for user creation script."""
    
    # Parse command line arguments
    if len(sys.argv) < 3:
        print("Usage: python create_user.py <email> <password> [--full-name 'Full Name']")
        print("")
        print("Example:")
        print("  python create_user.py user@example.com MyPassword123 --full-name 'John Doe'")
        print("")
        print("Options:")
        print("  --full-name   Optional full name for the user")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    
    # Parse optional full name
    full_name = None
    if len(sys.argv) >= 5 and sys.argv[3] == '--full-name':
        full_name = sys.argv[4]
    
    # Validate inputs
    if '@' not in email:
        logger.error(f"Invalid email address: {email}")
        sys.exit(1)
    
    if len(password) < 8:
        logger.error("Password must be at least 8 characters long")
        sys.exit(1)
    
    # Get database session
    try:
        settings = get_settings()
        logger.info(f"Settings loaded for environment: {settings.environment}")
        
        engine = get_engine()
        logger.info("Database engine created")
        
        SessionLocal = get_session_local()
        db = SessionLocal()
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        sys.exit(2)
    
    # Create the user
    try:
        success = create_user(email, password, full_name, db)
        
        if success:
            sys.exit(0)  # Success
        else:
            logger.error("")
            logger.error("❌ User creation failed - see logs above")
            sys.exit(1)  # Failure
            
    finally:
        db.close()
        logger.info("Database session closed")


if __name__ == "__main__":
    main()
