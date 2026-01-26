
import os
import sys

# Add the backend directory to sys.path to resolve imports
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from ai_receptionist.core.database import get_engine, get_session_local
from ai_receptionist.models.base import Base
from ai_receptionist.models.business import Business
from ai_receptionist.models.oauth import GoogleOAuthToken

def init_db():
    print("Initializing database...")
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    
    SessionLocal = get_session_local()
    db = SessionLocal()
    
    # Check if a business exists
    biz = db.query(Business).first()
    if not biz:
        print("Creating default business...")
        biz = Business(
            name="My Awesome Business",
            phone_number="+15550001234",
            industry="Technology",
            description="Doing cool AI things"
        )
        db.add(biz)
        db.commit()
        db.refresh(biz)
        print(f"Created business with ID: {biz.id}")
    else:
        print(f"Business already exists: {biz.name} (ID: {biz.id})")
    
    db.close()
    print("Database initialization complete.")

if __name__ == "__main__":
    init_db()
