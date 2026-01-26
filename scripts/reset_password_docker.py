import sys
import os
import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup context
sys.path.append('/app')

try:
    from ai_receptionist.config.settings import get_settings
    from ai_receptionist.models.user import User
    from ai_receptionist.models.business import Business
except ImportError:
    print("Could not import app modules. Make sure you are running inside the container.")
    sys.exit(1)

settings = get_settings()
db_url = settings.get_database_url()
print(f"Connecting to DB: {db_url}")

engine = create_engine(db_url)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

email = "thegamermasterninja@gmail.com"
new_password = "ChangeMe123!"

print(f"Resetting password for {email}...")

try:
    user = session.query(User).filter(User.email == email).first()
    
    hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

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
                subscription_status="active"
            )
            session.add(biz)
        
        session.commit()
        print(f"✅ User created with password: {new_password}")
    else:
        user.password_hash = hashed
        user.is_active = True
        session.commit()
        print(f"✅ Password updated to: {new_password}")

except Exception as e:
    print(f"❌ Error: {e}")
finally:
    session.close()
