#!/usr/bin/env python3
"""Simple DB Check Script"""

import sys
sys.path.append('/app')

from ai_receptionist.core.database import get_db_session
from ai_receptionist.models.user import User
from ai_receptionist.models.business import Business

def main():
    print("📊 DATABASE CHECK")
    print("=" * 40)
    
    try:
        with get_db_session() as db:
            # Check target user
            user = db.query(User).filter(User.email == "thegamermasterninja@gmail.com").first()
            if user:
                print(f"👤 User: {user.email} (ID: {user.id})")
                
                # Check user's business
                business = db.query(Business).filter(Business.owner_email == user.email).first()
                if business:
                    print(f"🏢 Business: {business.name} (ID: {business.id})")
                    print(f"📞 Phone: {business.phone_number}")
                    print(f"🤖 Receptionist: {business.receptionist_enabled}")
                    print(f"✅ Active: {business.is_active}")
                else:
                    print("❌ No business found for user")
            else:
                print("❌ User not found")
                
    except Exception as e:
        print(f"💥 Error: {e}")
        return False
        
    print("✅ Check completed")
    return True

if __name__ == "__main__":
    main()