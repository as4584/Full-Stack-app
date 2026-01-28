"""
OAuth endpoints for Google Calendar integration.

Implements OAuth 2.0 flow for connecting Google Calendar accounts.
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse, JSONResponse
from urllib.parse import urlencode
from sqlalchemy.orm import Session
import logging
import httpx

from ai_receptionist.config.settings import Settings, get_settings
from ai_receptionist.core.database import get_db
from ai_receptionist.utils.encryption import encrypt_token
from ai_receptionist.models.oauth import GoogleOAuthToken

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/oauth", tags=["oauth"])


@router.get("/google/start")
def google_oauth_start(
    business_id: str = Query(..., description="Business/tenant ID to connect calendar for"),
    settings: Settings = Depends(get_settings),
):
    """
    Step 1: Initiate Google OAuth flow.
    
    Builds the Google authorization URL and redirects the user to it.
    The business_id is passed through the state parameter.
    
    Query Parameters:
        business_id: The tenant/business identifier to associate with this calendar
    
    Returns:
        RedirectResponse to Google's OAuth consent screen
    """
    # Validate required configuration
    if not settings.google_client_id:
        logger.warning("GOOGLE_CLIENT_ID not configured - calendar integration unavailable")
        return JSONResponse(
            status_code=200,
            content={
                "available": False,
                "error": "Google Calendar integration is not configured on this server",
                "detail": "Contact your administrator to enable Google Calendar integration"
            }
        )
    
    if not settings.google_redirect_uri:
        logger.warning("GOOGLE_REDIRECT_URI not configured - calendar integration unavailable")
        return JSONResponse(
            status_code=200,
            content={
                "available": False,
                "error": "Google Calendar redirect URI not configured",
                "detail": "Contact your administrator to enable Google Calendar integration"
            }
        )
    
    # Build Google OAuth authorization URL
    auth_params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/calendar",
        "access_type": "offline",
        "prompt": "consent",
        "state": business_id,  # Pass business_id through state param
    }
    
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(auth_params)}"
    
    logger.info(f"Redirecting to Google OAuth for business_id={business_id}")
    
    return RedirectResponse(url=auth_url, status_code=302)


@router.get("/google/callback")
async def google_oauth_callback(
    code: Optional[str] = Query(None),
    error: Optional[str] = Query(None),
    state: Optional[str] = Query(None, description="business_id passed from start"),
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
):
    """
    Step 2: Handle Google OAuth callback.
    
    Exchanges authorization code for tokens and saves them to the database
    atomically. The state parameter contains the business_id.
    
    Redirects back to the dashboard upon completion or failure.
    """
    dashboard_base = f"{settings.dashboard_url}/app"

    # Handle user cancellation or OAuth errors
    if error:
        logger.warning(f"OAuth cancelled or failed: {error}")
        return RedirectResponse(
            url=f"{dashboard_base}?error=calendar_cancelled&details={error}",
            status_code=302
        )
    
    if not code:
        logger.error("No authorization code received")
        return RedirectResponse(
            url=f"{dashboard_base}?error=calendar_failed&details=missing_code",
            status_code=302
        )
    
    # Validate state (business_id)
    if not state:
        logger.error("No state/business_id in callback")
        return RedirectResponse(
            url=f"{dashboard_base}?error=calendar_failed&details=missing_state",
            status_code=302
        )
    
    tenant_id = state
    
    # Validate configuration
    if not settings.google_client_id or not settings.google_client_secret:
        logger.error("Google OAuth credentials not configured")
        return RedirectResponse(
            url=f"{dashboard_base}?error=calendar_configuration_error",
            status_code=302
        )
    
    try:
        # Exchange authorization code for tokens
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "redirect_uri": settings.google_redirect_uri,
                    "grant_type": "authorization_code",
                },
                timeout=15.0,
            )
            
            if token_response.status_code != 200:
                logger.error(f"Token exchange failed: {token_response.text}")
                return RedirectResponse(
                    url=f"{dashboard_base}?error=calendar_token_exchange_failed",
                    status_code=302
                )
            
            token_data = token_response.json()
        
        # Extract tokens
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in", 3600)
        scope = token_data.get("scope", "")
        
        if not access_token:
            logger.error("No access token in response")
            return RedirectResponse(
                url=f"{dashboard_base}?error=calendar_no_access_token",
                status_code=302
            )
        
        if not refresh_token:
            logger.warning(f"No refresh token for {tenant_id} - connection may lose persistence")
        
        # Calculate expiration time
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        # Encrypt tokens
        access_token_encrypted = encrypt_token(access_token)
        refresh_token_encrypted = encrypt_token(refresh_token) if refresh_token else ""
        
        # Save to database atomically (upsert)
        existing = db.query(GoogleOAuthToken).filter(
            GoogleOAuthToken.tenant_id == tenant_id
        ).first()
        
        if existing:
            # Update existing record
            existing.access_token_encrypted = access_token_encrypted
            existing.refresh_token_encrypted = refresh_token_encrypted or existing.refresh_token_encrypted
            existing.expires_at = expires_at
            existing.scope = scope
            existing.is_connected = True
            existing.updated_at = datetime.utcnow()
            logger.info(f"Updated OAuth tokens for tenant {tenant_id}")
        else:
            # Create new record
            new_token = GoogleOAuthToken(
                tenant_id=tenant_id,
                access_token_encrypted=access_token_encrypted,
                refresh_token_encrypted=refresh_token_encrypted,
                expires_at=expires_at,
                scope=scope,
                is_connected=True,
            )
            db.add(new_token)
            logger.info(f"Created new OAuth tokens for tenant {tenant_id}")
        
        # Commit atomically
        db.commit()
        
        return RedirectResponse(
            url=f"{dashboard_base}?success=calendar_connected",
            status_code=302
        )
        
    except httpx.HTTPError as e:
        logger.error(f"HTTP error during token exchange: {e}")
        db.rollback()
        return RedirectResponse(
            url=f"{dashboard_base}?error=calendar_network_error",
            status_code=302
        )
    except Exception as e:
        logger.error(f"Unexpected error in OAuth callback: {e}", exc_info=True)
        db.rollback()
        return RedirectResponse(
            url=f"{dashboard_base}?error=calendar_internal_error",
            status_code=302
        )


@router.get("/google/status")
def google_oauth_status(
    business_id: str = Query(..., description="Business/tenant ID to check"),
    db: Session = Depends(get_db),
):
    """
    Check if a business has a connected Google Calendar.
    
    Query Parameters:
        business_id: The tenant/business identifier
        
    Returns:
        Connection status and expiration info
    """
    try:
        token = db.query(GoogleOAuthToken).filter(
            GoogleOAuthToken.tenant_id == business_id
        ).first()
    except Exception as e:
        logger.error(f"Database error checking OAuth status for {business_id}: {e}")
        return {
            "connected": False,
            "error": "database_error",
            "detail": str(e),
            "message": "Encountered a database error while checking calendar status."
        }
    
    if not token:
        return {
            "connected": False,
            "message": "No Google Calendar connected",
        }
    
    if not token.is_connected:
        return {
            "connected": False,
            "message": "Google Calendar was disconnected",
        }
    
    is_expired = token.expires_at < datetime.utcnow()
    has_refresh = bool(token.refresh_token_encrypted)
    
    return {
        "connected": True,
        "message": "Google Calendar is connected",
        "expires_at": token.expires_at.isoformat(),
        "is_expired": is_expired,
        "can_refresh": has_refresh,
        "scope": token.scope,
    }


@router.post("/google/disconnect")
def google_oauth_disconnect(
    business_id: str = Query(..., description="Business/tenant ID to disconnect"),
    db: Session = Depends(get_db),
):
    """
    Disconnect a business's Google Calendar.
    
    This marks the connection as inactive but does not delete the record.
    """
    token = db.query(GoogleOAuthToken).filter(
        GoogleOAuthToken.tenant_id == business_id
    ).first()
    
    if not token:
        return {"success": True, "message": "No calendar was connected"}
    
    token.is_connected = False
    token.updated_at = datetime.utcnow()
    db.commit()
    
    logger.info(f"Disconnected Google Calendar for tenant {business_id}")
    
    return {"success": True, "message": "Google Calendar disconnected"}

