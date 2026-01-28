"""
API Authentication middleware using JWT and admin private key.

This allows secure communication between frontend and backend servers.
Supports both Bearer token (Authorization header) and HTTP-only cookie authentication.
"""
import jwt
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import HTTPException, Security, Depends, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from ai_receptionist.config.settings import get_settings

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)  # Don't auto-error, we'll check cookie too

# Cookie configuration
ACCESS_TOKEN_COOKIE_NAME = "lex_token"
ACCESS_TOKEN_EXPIRE_DAYS = 7


class TokenData(BaseModel):
    """JWT token payload."""
    user_id: Optional[int] = None
    email: Optional[str] = None
    business_id: Optional[str] = None
    exp: Optional[datetime] = None


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Payload to encode in token
        expires_delta: Token expiration time (default: 7 days)
        
    Returns:
        Encoded JWT token
    """
    settings = get_settings()
    
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire})
    
    # Use ADMIN_PRIVATE_KEY as JWT secret (no fallback - must be set)
    if not settings.admin_private_key:
        raise RuntimeError(
            "CRITICAL: ADMIN_PRIVATE_KEY not configured. "
            "JWT tokens cannot be created without a persistent secret. "
            "Set ADMIN_PRIVATE_KEY in .env file."
        )
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.admin_private_key,
        algorithm="HS256"
    )
    
    return encoded_jwt


def verify_token(token: str) -> TokenData:
    """
    Verify and decode JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token data
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    settings = get_settings()
    
    try:
        # Use ADMIN_PRIVATE_KEY as JWT secret (no fallback - must be set)
        if not settings.admin_private_key:
            logger.error("[AUTH] CRITICAL: ADMIN_PRIVATE_KEY not configured - JWT verification impossible")
            raise HTTPException(
                status_code=500,
                detail="Authentication service misconfigured"
            )
        
        payload = jwt.decode(
            token,
            settings.admin_private_key,
            algorithms=["HS256"]
        )
        
        logger.debug(f"[AUTH] JWT verified successfully for user_id={payload.get('user_id')}")
        return TokenData(**payload)
        
    except jwt.ExpiredSignatureError as e:
        logger.warning(f"[AUTH] JWT expired: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"[AUTH] JWT invalid: {str(e)[:100]}")
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials"
        )


def set_auth_cookie(response: Response, token: str) -> None:
    """
    Set the access_token cookie for cross-subdomain authentication.
    
    Cookie settings:
    - Domain=.lexmakesit.com (accessible by all subdomains)
    - Path=/
    - SameSite=Lax (allows top-level navigations from external sites)
    - Secure=True (in production, HTTPS only)
    - HttpOnly=True (not accessible by JavaScript)
    """
    settings = get_settings()
    
    # Calculate max_age in seconds (7 days)
    max_age = ACCESS_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    
    # In production, use the root domain for cross-subdomain cookies
    # In development, don't set domain (allows localhost)
    if settings.is_production:
        cookie_domain = ".lexmakesit.com"
    else:
        cookie_domain = None  # Don't set domain for localhost
    
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE_NAME,
        value=token,
        max_age=max_age,
        path="/",
        domain=cookie_domain,
        secure=settings.is_production,  # Secure only in production (HTTPS)
        httponly=True,  # Not accessible via JavaScript
        samesite="lax"  # Allows top-level navigations
    )
    
    # TEMPORARY VERIFICATION LOG - Remove after confirming cookie setup works
    logger.info(
        f"[AUTH-COOKIE] Set cookie: domain={cookie_domain}, "
        f"secure={settings.is_production}, httponly=True, samesite=lax, "
        f"max_age={max_age}s ({ACCESS_TOKEN_EXPIRE_DAYS} days), "
        f"is_production={settings.is_production}"
    )


def clear_auth_cookie(response: Response) -> None:
    """
    Clear the access_token cookie (logout).
    """
    settings = get_settings()
    
    if settings.is_production:
        cookie_domain = ".lexmakesit.com"
    else:
        cookie_domain = None
    
    response.delete_cookie(
        key=ACCESS_TOKEN_COOKIE_NAME,
        path="/",
        domain=cookie_domain
    )


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> TokenData:
    """
    FastAPI dependency to get current authenticated user.
    
    Tries in order:
    1. Bearer token from Authorization header
    2. access_token from HTTP-only cookie
    
    Usage:
        @app.get("/protected")
        async def protected_route(user: TokenData = Depends(get_current_user)):
            return {"user_id": user.user_id}
    """
    token = None
    
    # Try Authorization header first
    if credentials and credentials.credentials:
        token = credentials.credentials
        logger.debug(f"[AUTH] Token from Authorization header")
    
    # Fall back to cookie
    if not token:
        token = request.cookies.get(ACCESS_TOKEN_COOKIE_NAME)
        if token:
            logger.debug(f"[AUTH] Token from cookie: {ACCESS_TOKEN_COOKIE_NAME}")
        else:
            # Log all cookies for debugging
            all_cookies = list(request.cookies.keys())
            logger.warning(f"[AUTH] No token found. Available cookies: {all_cookies}")
    
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )
    
    return verify_token(token)


async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> Optional[TokenData]:
    """
    Optional version of get_current_user that returns None instead of raising.
    
    Useful for endpoints that work with or without authentication.
    """
    try:
        return await get_current_user(request, credentials)
    except HTTPException:
        return None


async def get_current_business_id(
    user: TokenData = Depends(get_current_user)
) -> str:
    """
    Get business_id from authenticated user.
    
    Raises HTTPException if no business_id in token.
    """
    if not user.business_id:
        raise HTTPException(
            status_code=403,
            detail="No business associated with this account"
        )
    
    return user.business_id
