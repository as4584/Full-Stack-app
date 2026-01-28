#!/usr/bin/env python3
"""
Quick Database Verification Script
Checks current state of users and businesses
"""

import sys
sys.path.append('/app')  # Docker container path

from ai_receptionist.core.database import get_db_session
from ai_receptionist.models.user import User
from ai_receptionist.models.business import Business

def check_database_state():
    """Check current database state."""
    
    print("🔍 DATABASE STATE CHECK")
    print("=" * 50)
    
    try:
        with get_db_session() as db:
            # Check users
            users = db.query(User).all()
            print(f"📊 Total Users: {len(users)}")
            for user in users:
                print(f"   • ID: {user.id}, Email: {user.email}, Active: {user.is_active}")
            
            # Check businesses  
            businesses = db.query(Business).all()
            print(f"🏢 Total Businesses: {len(businesses)}")
            for business in businesses:
                print(f"   • ID: {business.id}, Owner: {business.owner_email}")
                print(f"     Name: {business.name}")
                print(f"     Phone: {business.phone_number}")
                print(f"     Receptionist Enabled: {business.receptionist_enabled}")
                print(f"     Active: {business.is_active}")
                print()
            
            # Check relationships
            target_email = "thegamermasterninja@gmail.com"
            target_user = db.query(User).filter(User.email == target_email).first()
            if target_user:
                user_businesses = db.query(Business).filter(Business.owner_email == target_email).all()
                print(f"👤 User {target_email} has {len(user_businesses)} business(es)")
                for biz in user_businesses:
                    print(f"   • Business: {biz.name} (Phone: {biz.phone_number})")
                    
        print("✅ Database check completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    check_database_state()