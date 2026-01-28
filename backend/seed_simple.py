#!/usr/bin/env python3
"""
Simple AI Receptionist Business Data Seed - Minimal Version
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add backend to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

print("🌱 Simple Business Seeding Started")

try:
    print("Importing database...")
    from ai_receptionist.core.database import get_db_session
    print("✅ Database import OK")
    
    print("Importing User model...")
    from ai_receptionist.models.user import User
    print("✅ User import OK")
    
    print("Importing Business model...")
    from ai_receptionist.models.business import Business  
    print("✅ Business import OK")
    
    print("Testing database connection...")
    with get_db_session() as db:
        print("✅ Database connection OK")
        
        # Check if user exists
        email = "thegamermasterninja@gmail.com"
        user = db.query(User).filter(User.email == email).first()
        
        if user:
            print(f"✅ User {email} already exists (ID: {user.id})")
        else:
            print(f"Creating user {email}...")
            user = User()
            user.email = email
            user.is_active = True
            user.is_verified = True
            user.password_hash = "temp_hash_placeholder"
            db.add(user)
            db.flush()
            print(f"✅ User created (ID: {user.id})")
        
        # Check business
        business = db.query(Business).filter(Business.owner_email == email).first()
        
        if business:
            print(f"✅ Business already exists (ID: {business.id})")
            # Update key fields
            business.name = "AI Assistant Service"
            business.phone_number = "+1234567890"
            business.is_active = True
            business.receptionist_enabled = True
        else:
            print("Creating business...")
            business = Business()
            business.owner_email = email
            business.name = "AI Assistant Service"
            business.phone_number = "+1234567890"
            business.industry = "Technology Consulting"
            business.description = "Professional AI-powered receptionist service"
            business.is_active = True
            business.receptionist_enabled = True
            db.add(business)
            db.flush()
            print(f"✅ Business created (ID: {business.id})")

    print("🎉 SEEDING COMPLETED SUCCESSFULLY!")
    print(f"   User: {email}")
    print(f"   Business: AI Assistant Service")
    print("   ✅ Data is persistent in PostgreSQL")
    
except Exception as e:
    print(f"❌ SEEDING FAILED: {e}")
    sys.exit(1)