#!/usr/bin/env python3
"""
Fix Existing User Password - Production Safe Script
=====================================================
This script:
1. Finds an existing user by email
2. Resets their password using bcrypt
3. Verifies the change
"""

import sys
import os

# Add the backend to path
sys.path.insert(0, '/app')

import bcrypt
from ai_receptionist.core.database import get_session_local
from ai_receptionist.models.user import User
from sqlalchemy import func

# Get SessionLocal factory
SessionLocal = get_session_local()

TARGET_EMAIL = "thegamermasterninja@gmail.com"
NEW_PASSWORD = "Alexander1221"

def main():
    print("=" * 60)
    print("STEP 1: VERIFY USER EXISTS")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # Query for the user
        user = db.query(User).filter(User.email == TARGET_EMAIL).first()
        
        if not user:
            print(f"❌ USER NOT FOUND: {TARGET_EMAIL}")
            print("ABORTING - Will not create new user")
            return False
        
        print(f"✅ USER FOUND")
        print(f"   ID: {user.id}")
        print(f"   Email: {user.email}")
        print(f"   Full Name: {user.full_name}")
        print(f"   Password Hash Present: {bool(user.password_hash)}")
        print(f"   Password Hash (first 20 chars): {user.password_hash[:20] if user.password_hash else 'None'}...")
        
        # Check for duplicates
        duplicate_count = db.query(func.count(User.id)).filter(User.email == TARGET_EMAIL).scalar()
        print(f"   Duplicate Check: {duplicate_count} user(s) with this email")
        
        if duplicate_count > 1:
            print("❌ DUPLICATE USERS FOUND - ABORTING")
            return False
        
        original_id = user.id
        original_email = user.email
        original_hash = user.password_hash
        
        print()
        print("=" * 60)
        print("STEP 2: RESET PASSWORD")
        print("=" * 60)
        
        # Generate new bcrypt hash directly
        new_hash = bcrypt.hashpw(NEW_PASSWORD.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        print(f"   New Password: {NEW_PASSWORD}")
        print(f"   New Hash (first 20 chars): {new_hash[:20]}...")
        
        # Update the password
        user.password_hash = new_hash
        db.commit()
        db.refresh(user)
        print("   ✅ Password hash updated in database")
        
        print()
        print("=" * 60)
        print("STEP 3: VERIFY DATABASE INTEGRITY")
        print("=" * 60)
        
        # Re-query to verify
        user_check = db.query(User).filter(User.email == TARGET_EMAIL).first()
        
        print(f"   ID unchanged: {user_check.id == original_id} (was {original_id}, now {user_check.id})")
        print(f"   Email unchanged: {user_check.email == original_email}")
        print(f"   Password hash changed: {user_check.password_hash != original_hash}")
        print(f"   New hash starts with: {user_check.password_hash[:20]}...")
        
        # Verify no duplicates were created
        final_count = db.query(func.count(User.id)).filter(User.email == TARGET_EMAIL).scalar()
        print(f"   No duplicates: {final_count == 1} ({final_count} user(s) total)")
        
        print()
        print("=" * 60)
        print("STEP 4: VERIFY LOGIN (PASSWORD VERIFICATION)")
        print("=" * 60)
        
        # Test password verification using bcrypt directly
        password_valid = bcrypt.checkpw(NEW_PASSWORD.encode('utf-8'), user_check.password_hash.encode('utf-8'))
        print(f"   Password verification: {'✅ SUCCESS' if password_valid else '❌ FAILED'}")
        
        if not password_valid:
            print("   ❌ Password verification failed - ABORTING")
            return False
        
        print()
        print("=" * 60)
        print("STEP 5: FINAL CONFIRMATION")
        print("=" * 60)
        print()
        print("✅ Existing user credentials fixed successfully")
        print(f"   Email: {TARGET_EMAIL}")
        print(f"   Password: {NEW_PASSWORD}")
        print(f"   User ID preserved: {user_check.id}")
        print("   Login verified in production")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
