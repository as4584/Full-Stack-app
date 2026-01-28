#!/usr/bin/env python3
"""
Simple Business Seed Script - FIXED VERSION
Creates business with phone number +12298215986
"""

import sys
import os

# Add paths for container and local
sys.path.append('/app')
sys.path.append('/home/lex/lexmakesit/backend')

from ai_receptionist.core.database import get_db_session
from ai_receptionist.models.user import User
from ai_receptionist.models.business import Business

def main():
    target_email = "thegamermasterninja@gmail.com"
    target_phone = "+12298215986"
    
    print("🔍 Starting business creation...")
    print(f"Target email: {target_email}")
    print(f"Target phone: {target_phone}")
    
    try:
        with get_db_session() as db:
            # Find user
            user = db.query(User).filter(User.email == target_email).first()
            if not user:
                print("❌ User not found!")
                return False
                
            print(f"✅ Found user ID: {user.id}")
            
            # Check existing business
            existing = db.query(Business).filter(Business.owner_email == target_email).first()
            
            if existing:
                print(f"🔄 Updating existing business ID: {existing.id}")
                existing.phone_number = target_phone
                existing.receptionist_enabled = True
                existing.is_active = 1
                business = existing
            else:
                print("🆕 Creating new business")
                business = Business()
                business.owner_email = target_email
                business.name = "AI Receptionist Business"
                business.phone_number = target_phone
                business.industry = "Technology"
                business.description = "AI-powered customer service"
                business.receptionist_enabled = True
                business.is_active = 1
                business.greeting_style = "professional"
                business.business_hours = "9:00 AM - 5:00 PM EST"
                business.timezone = "America/New_York"
                business.common_services = "Customer support, appointment scheduling"
                business.faqs = []
                business.subscription_status = "active"
                business.audit_status = "verified"
                db.add(business)
            
            db.commit()
            print(f"💾 SUCCESS! Business ID: {business.id}")
            print(f"📞 Phone number: {business.phone_number}")
            print(f"🤖 Receptionist enabled: {business.receptionist_enabled}")
            
            return True
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 BUSINESS SEEDING COMPLETED!")
    else:
        print("\n💥 BUSINESS SEEDING FAILED!")
        sys.exit(1)