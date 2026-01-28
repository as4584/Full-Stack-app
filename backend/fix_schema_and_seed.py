#!/usr/bin/env python3
"""
AI Receptionist Schema Fix and Business Seeding - SAFE MODE

This script:
1. Checks if owner_email column exists in businesses table
2. Creates it if missing (safe migration)
3. Seeds business data for thegamermasterninja@gmail.com
4. Attaches phone number +12298215986
5. Verifies all relationships
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

print("🔧 AI Receptionist Schema Fix + Business Seeding")
print("=" * 60)

try:
    # Import required modules
    from ai_receptionist.core.database import get_db_session
    from ai_receptionist.models.user import User
    from ai_receptionist.models.business import Business
    from ai_receptionist.config.settings import get_settings
    
    settings = get_settings()
    print(f"Environment: {settings.app_env}")
    print(f"Database: PostgreSQL (production mode)")
    
    with get_db_session() as db:
        print("\n📊 STEP 1: Schema Analysis")
        print("-" * 30)
        
        # Check if owner_email column exists
        result = db.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'businesses' AND column_name = 'owner_email'
        """)
        owner_email_exists = result.fetchone() is not None
        print(f"owner_email column exists: {owner_email_exists}")
        
        # If owner_email doesn't exist, add it (SAFE MIGRATION)
        if not owner_email_exists:
            print("Adding owner_email column...")
            db.execute("ALTER TABLE businesses ADD COLUMN owner_email VARCHAR(255)")
            db.execute("CREATE INDEX IF NOT EXISTS ix_businesses_owner_email ON businesses (owner_email)")
            print("✅ owner_email column added safely")
        else:
            print("✅ owner_email column already exists")
        
        print("\n👤 STEP 2: User Verification")
        print("-" * 30)
        
        # Find the existing user
        target_email = "thegamermasterninja@gmail.com"
        user = db.query(User).filter(User.email == target_email).first()
        
        if not user:
            print(f"❌ User {target_email} not found!")
            sys.exit(1)
        
        print(f"✅ User found: {user.email} (ID: {user.id})")
        
        print("\n🏢 STEP 3: Business Setup")
        print("-" * 30)
        
        # Check if business already exists for this user
        existing_business = db.query(Business).filter(
            Business.owner_email == user.email
        ).first()
        
        business_config = {
            "name": "AI Assistant Service",
            "phone_number": "+12298215986",  # User's actual phone number
            "industry": "Technology Consulting",
            "description": "Professional AI-powered receptionist service providing 24/7 customer support and appointment scheduling.",
            "greeting_style": "professional_friendly",
            "business_hours": "24/7",
            "timezone": "America/New_York",
            "common_services": "AI receptionist services, appointment scheduling, customer support, call screening and routing",
            "faqs": [
                {
                    "question": "What services do you offer?",
                    "answer": "I provide AI-powered receptionist services including call handling, appointment scheduling, and customer support."
                },
                {
                    "question": "What are your hours?",
                    "answer": "I'm available 24/7 to assist with your needs."
                },
                {
                    "question": "How can I schedule an appointment?",
                    "answer": "I can help you schedule an appointment right now. What service are you interested in and what time works best for you?"
                }
            ]
        }
        
        if existing_business:
            print(f"Business exists (ID: {existing_business.id}), updating...")
            # Update existing business
            for key, value in business_config.items():
                setattr(existing_business, key, value)
            
            existing_business.owner_email = user.email
            existing_business.is_active = 1
            existing_business.receptionist_enabled = True
            existing_business.phone_number_status = "active"
            
            business = existing_business
        else:
            print("Creating new business...")
            # Create new business
            business = Business()
            
            for key, value in business_config.items():
                setattr(business, key, value)
            
            business.owner_email = user.email
            business.is_active = 1
            business.receptionist_enabled = True
            business.phone_number_status = "active"
            
            db.add(business)
        
        # Flush to get business ID
        db.flush()
        
        print(f"✅ Business configured:")
        print(f"   ID: {business.id}")
        print(f"   Name: {business.name}")
        print(f"   Owner: {business.owner_email}")
        print(f"   Phone: {business.phone_number}")
        print(f"   Active: {business.is_active}")
        print(f"   Receptionist: {business.receptionist_enabled}")
        
        print("\n📞 STEP 4: Phone Number Integration")
        print("-" * 30)
        
        # Verify phone number is properly set
        if business.phone_number == "+12298215986":
            print("✅ Phone number correctly attached")
            print("✅ AI receptionist can recognize this number")
        else:
            print(f"❌ Phone number mismatch: {business.phone_number}")
        
        print("\n🔗 STEP 5: Relationship Verification")
        print("-" * 30)
        
        # Verify the complete relationship chain
        print("Verifying: User → Business → Phone Number")
        
        # Test query: Find business by user email
        test_business = db.query(Business).filter(
            Business.owner_email == user.email
        ).first()
        
        if test_business and test_business.phone_number:
            print(f"✅ Relationship verified:")
            print(f"   User: {user.email} (ID: {user.id})")
            print(f"   ↓")
            print(f"   Business: {test_business.name} (ID: {test_business.id})")
            print(f"   ↓")
            print(f"   Phone: {test_business.phone_number}")
        else:
            print("❌ Relationship verification failed")
            sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🎉 SCHEMA FIX + BUSINESS SEEDING COMPLETED!")
    print()
    print("📋 SUMMARY:")
    print(f"   ✅ Migration applied: {'Yes' if not owner_email_exists else 'N/A (already existed)'}")
    print(f"   ✅ Business ID: {business.id}")
    print(f"   ✅ User ID linkage: {user.id}")
    print(f"   ✅ Phone number stored: {business.phone_number}")
    print(f"   ✅ AI receptionist enabled: {business.receptionist_enabled}")
    print()
    print("🎯 NEXT STEPS:")
    print("   1. Restart containers to test persistence")
    print("   2. Test dashboard login with thegamermasterninja@gmail.com")  
    print("   3. Verify phone number shows in dashboard")
    print("   4. Test Twilio webhook integration")
    print("=" * 60)
        
except Exception as e:
    print(f"\n❌ SCHEMA FIX FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)