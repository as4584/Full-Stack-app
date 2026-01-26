import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from ai_receptionist.config.settings import get_settings
from ai_receptionist.models.business import Business
# Assuming User model exists, let's try to find it. 
# Based on previous file lists, it might be in ai_receptionist.models.user or part of auth.
# Let's just query the 'users' table directly using SQL for safety if model import fails.

settings = get_settings()
db_url = settings.get_database_url()
print(f"Connecting to {db_url}")

engine = create_engine(db_url)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

try:
    email = "thegamermasterninja@gmail.com"
    print(f"Checking for user: {email}")
    
    # Check Business (since auth seems tied to Business owner_email currently?)
    # Wait, the auth system was previously shown in main.py importing specific auth routes.
    # Let's check the 'users' table if it exists.
    
    result = session.execute(text("SELECT * FROM users WHERE email = :email"), {"email": email}).fetchone()
    if result:
        print(f"✅ User found in 'users' table: {result}")
    else:
        print(f"❌ User NOT found in 'users' table")

    # Check Business table
    result_biz = session.execute(text("SELECT * FROM businesses WHERE owner_email = :email"), {"email": email}).fetchone()
    if result_biz:
         print(f"✅ Business found for email: {result_biz}")
    else:
         print(f"❌ Business NOT found for email")

except Exception as e:
    print(f"Error: {e}")
finally:
    session.close()
