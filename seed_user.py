import sys
import os
import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the backend directory to sys.path to allow imports
sys.path.append('/home/lex/lexmakesit/backend')

from ai_receptionist.models.user import User
from ai_receptionist.models.business import Business
from ai_receptionist.models.base import Base

# Database path
db_url = "sqlite:///backend/sql_app.db"
engine = create_engine(db_url)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

email = "thegamermasterninja@gmail.com"
password = "ChangeMe123!"

print(f"Ensuring user {email} exists in {db_url}...")

try:
    # Ensure tables exist (in case they don't)
    Base.metadata.create_all(bind=engine)
    
    user = session.query(User).filter(User.email == email).first()
    # Use cost 10 for compatibility/speed
    salt = bcrypt.gensalt(10)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    print(f"Generated hash: {hashed}")
    
    # Verify immediately
    if bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8')):
        print("✅ Immediate verification passed.")
    else:
        print("❌ Immediate verification FAILED.")

    if not user:
        print("User not found! Creating user...")
        user = User(
            email=email, 
            password_hash=hashed, 
            full_name="Admin User", 
            is_verified=True, 
            is_active=True
        )
        session.add(user)
        session.flush() # Get ID
        
        # Check Business
        biz = session.query(Business).filter(Business.owner_email == email).first()
        if not biz:
            print("Creating business...")
            biz = Business(
                owner_email=email,
                name="Admin Business",
                subscription_status="active",
                receptionist_enabled=True,
                is_active=1
            )
            session.add(biz)
        
        session.commit()
        print(f"✅ User created successfully.")
    else:
        print("User already exists. Updating password...")
        user.password_hash = hashed
        user.is_active = True
        user.is_verified = True
        
        # Ensure business exists
        biz = session.query(Business).filter(Business.owner_email == email).first()
        if not biz:
            print("Creating missing business...")
            biz = Business(
                owner_email=email,
                name="Admin Business",
                subscription_status="active",
                receptionist_enabled=True,
                is_active=1
            )
            session.add(biz)
        else:
            biz.is_active = 1
            biz.receptionist_enabled = True
            
        session.commit()
        print(f"✅ User and Business updated successfully.")

except Exception as e:
    print(f"❌ Error: {e}")
    session.rollback()
finally:
    session.close()
