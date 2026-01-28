
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ai_receptionist.core.database import get_db
from ai_receptionist.models.business import Business
# from ai_receptionist.app.deps import get_current_user

router = APIRouter()

@router.post("/oauth/google/magic-connect")
async def magic_connect_google(
    business_id: str,
    db: Session = Depends(get_db),
):
    """
    Magic endpoint for Dev/Demo: Instantly connects Google Calendar 
    without real OAuth flow.
    """
    from ai_receptionist.models.oauth import GoogleOAuthToken
    from ai_receptionist.models.business import Business
    from datetime import datetime, timedelta

    business = db.query(Business).filter(Business.id == int(business_id)).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    
    # Simulate connection by creating/updating OAuth token record
    token = db.query(GoogleOAuthToken).filter(GoogleOAuthToken.tenant_id == str(business_id)).first()
    
    expires_at = datetime.utcnow() + timedelta(days=365)
    
    if token:
        token.is_connected = True
        token.expires_at = expires_at
        token.scope = "https://www.googleapis.com/auth/calendar"
    else:
        token = GoogleOAuthToken(
            tenant_id=str(business_id),
            access_token_encrypted=b"magic_token", # Dummy
            refresh_token_encrypted=b"magic_refresh", # Dummy
            expires_at=expires_at,
            scope="https://www.googleapis.com/auth/calendar",
            is_connected=True
        )
        db.add(token)
    
    db.commit()
    
    return {"status": "success", "message": "Magic Google Calendar Connection Successful"}
