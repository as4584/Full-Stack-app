#!/usr/bin/env python3
"""
AI Receptionist Business Data Seed Script

This script restores the original AI Receptionist business configuration
safely and reproducibly. It can be run multiple times safely.

Usage:
    python seed_business_data.py

Environment Variables Required:
    - DATABASE_URL or PostgreSQL connection details
    - TWILIO_* configuration (optional for phone setup)
"""

import os
import sys
import logging
from datetime import datetime, timezone
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from ai_receptionist.core.database import get_db_session
from ai_receptionist.models.user import User
from ai_receptionist.models.business import Business
from ai_receptionist.config.settings import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ORIGINAL AI RECEPTIONIST CONFIGURATION
BUSINESS_CONFIG = {
    "owner_email": "thegamermasterninja@gmail.com",
    "business_name": "AI Assistant Service",  # Replace with actual business name
    "phone_number": "+12298215986",  # Actual Twilio number
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

USER_CONFIG = {
    "email": "thegamermasterninja@gmail.com",
    "is_active": True,
    "is_verified": True
}


def ensure_database_connection():
    """Verify database connection and configuration."""
    try:
        settings = get_settings()
        db_url = settings.get_database_url()
        
        if not db_url:
            raise RuntimeError("No database URL configured")
            
        if db_url.startswith('sqlite') and settings.is_production:
            raise RuntimeError("SQLite detected in production - this should not happen!")
            
        logger.info(f"Database: {db_url.split('@')[0]}@****" if '@' in db_url else db_url[:50])
        return True
        
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False


def create_or_update_user(db_session) -> User:
    """Create or update the main user account."""
    logger.info(f"Setting up user: {USER_CONFIG['email']}")
    
    try:
        # Check if user exists
        logger.info("Checking for existing user...")
        existing_user = db_session.query(User).filter(User.email == USER_CONFIG["email"]).first()
        logger.info("Query completed successfully")
        
        if existing_user:
            logger.info(f"User {USER_CONFIG['email']} already exists (ID: {existing_user.id})")
            # Update user properties if needed
            existing_user.is_active = USER_CONFIG["is_active"]
            existing_user.is_verified = USER_CONFIG["is_verified"]
            return existing_user
        else:
            # Create new user
            logger.info("Creating new user...")
            new_user = User()
            # Set attributes manually to avoid __init__ restrictions
            new_user.email = USER_CONFIG["email"]
            new_user.is_active = USER_CONFIG["is_active"]  
            new_user.is_verified = USER_CONFIG["is_verified"]
            new_user.password_hash = "placeholder_hash"  # Required field
            logger.info("Adding user to session...")
            db_session.add(new_user)
            logger.info("Flushing session to get ID...")
            db_session.flush()  # Get ID
            logger.info(f"Created new user {USER_CONFIG['email']} (ID: {new_user.id})")
            return new_user
    except Exception as e:
        logger.error(f"Error in create_or_update_user: {e}")
        raise


def create_or_update_business(db_session, user: User) -> Business:
    """Create or update the AI Receptionist business."""
    logger.info(f"Setting up business: {BUSINESS_CONFIG['business_name']}")
    
    # Check if business exists for this user
    existing_business = db_session.query(Business).filter(
        Business.owner_email == user.email
    ).first()
    
    current_time = datetime.now(timezone.utc)
    
    if existing_business:
        logger.info(f"Business '{existing_business.name}' already exists (ID: {existing_business.id})")
        
        # Update business with original configuration
        existing_business.name = BUSINESS_CONFIG["business_name"]
        existing_business.phone_number = BUSINESS_CONFIG["phone_number"]
        existing_business.industry = BUSINESS_CONFIG["industry"]
        existing_business.description = BUSINESS_CONFIG["description"]
        existing_business.greeting_style = BUSINESS_CONFIG["greeting_style"]
        existing_business.business_hours = BUSINESS_CONFIG["business_hours"]
        existing_business.timezone = BUSINESS_CONFIG["timezone"]
        existing_business.common_services = BUSINESS_CONFIG["common_services"]
        existing_business.faqs = BUSINESS_CONFIG["faqs"]
        existing_business.is_active = True
        existing_business.receptionist_enabled = True
        
        logger.info(f"Updated business configuration for '{existing_business.name}'")
        return existing_business
    else:
        # Create new business
        new_business = Business(
            owner_email=user.email,
            name=BUSINESS_CONFIG["business_name"],
            phone_number=BUSINESS_CONFIG["phone_number"],
            industry=BUSINESS_CONFIG["industry"],
            description=BUSINESS_CONFIG["description"],
            greeting_style=BUSINESS_CONFIG["greeting_style"],
            business_hours=BUSINESS_CONFIG["business_hours"],
            timezone=BUSINESS_CONFIG["timezone"],
            common_services=BUSINESS_CONFIG["common_services"],
            faqs=BUSINESS_CONFIG["faqs"],
            is_active=True,
            receptionist_enabled=True,
            created_at=current_time
        )
        db_session.add(new_business)
        db_session.flush()  # Get ID
        logger.info(f"Created new business '{new_business.name}' (ID: {new_business.id})")
        return new_business


def verify_seed_success(db_session, user: User, business: Business):
    """Verify the seeding was successful."""
    logger.info("Verifying seed results...")
    
    # Verify user
    db_user = db_session.query(User).filter(User.email == user.email).first()
    assert db_user is not None, f"User {user.email} not found in database"
    assert db_user.is_active == True, f"User {user.email} is not active"
    
    # Verify business
    db_business = db_session.query(Business).filter(Business.id == business.id).first()
    assert db_business is not None, f"Business ID {business.id} not found in database"
    assert db_business.name == BUSINESS_CONFIG["business_name"], f"Business name mismatch"
    assert db_business.phone_number == BUSINESS_CONFIG["phone_number"], f"Phone number mismatch"
    assert db_business.is_active == True, f"Business is not active"
    assert db_business.receptionist_enabled == True, f"Receptionist not enabled"
    
    logger.info("✅ Seed verification successful!")
    logger.info(f"   User: {db_user.email} (ID: {db_user.id})")
    logger.info(f"   Business: {db_business.name} (ID: {db_business.id})")
    logger.info(f"   Phone: {db_business.phone_number}")
    logger.info(f"   Status: {'Active' if db_business.is_active else 'Inactive'}")


def main():
    """Main seeding function."""
    print("🌱 AI Receptionist Business Data Seeding Started")
    print("=" * 60)
    
    try:
        # 1. Check database connection
        if not ensure_database_connection():
            sys.exit(1)
            
        print("✅ Database connection verified")
        
        # 2. Seed data within transaction
        with get_db_session() as db:
            # Create/update user
            user = create_or_update_user(db)
            
            # Create/update business
            business = create_or_update_business(db, user)
            
            # Verify everything worked
            verify_seed_success(db, user, business)
            
        print("=" * 60)
        print("🎉 AI RECEPTIONIST BUSINESS DATA RESTORED SUCCESSFULLY!")
        print(f"   Business: {BUSINESS_CONFIG['business_name']}")
        print(f"   Owner: {USER_CONFIG['email']}")
        print(f"   Phone: {BUSINESS_CONFIG['phone_number']}")
        print("   ✅ Data is now persistent across restarts")
        print("   ✅ PostgreSQL ensures no data loss")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"Seeding failed: {e}")
        print("❌ SEEDING FAILED - Check logs above")
        sys.exit(1)


if __name__ == "__main__":
    main()