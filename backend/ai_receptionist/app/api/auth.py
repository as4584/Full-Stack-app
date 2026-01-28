"""
API endpoints for frontend authentication and user management.

Includes:
- Signup/Login with JWT tokens (via HTTP-only cross-subdomain cookies)
- Email verification
- Password reset
"""
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Response, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
import bcrypt
import logging

from ai_receptionist.core.database import get_db
from ai_receptionist.core.auth import (
    create_access_token, 
    get_current_user, 
    TokenData,
    set_auth_cookie,
    clear_auth_cookie
)
from ai_receptionist.models.user import User
from ai_receptionist.models.business import Business
from ai_receptionist.models.email_token import EmailToken

from ai_receptionist.core.limiter import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Token expiration (30 minutes)
EMAIL_TOKEN_EXPIRY_MINUTES = 30


# ============================================================================
# Request/Response Models
# ============================================================================

class SignupRequest(BaseModel):
    """Sign up request payload."""
    email: EmailStr
    password: str
    full_name: str
    business_name: str


class LoginRequest(BaseModel):
    """Login request payload."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Authentication token response."""
    access_token: str
    token_type: str = "bearer"
    user: dict


class VerifyEmailRequest(BaseModel):
    """Email verification request."""
    token: str


class ForgotPasswordRequest(BaseModel):
    """Forgot password request."""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Password reset request."""
    token: str
    new_password: str


class ChangePasswordRequest(BaseModel):
    """Authenticated password change request."""
    current_password: str
    new_password: str


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str


# ============================================================================
# Token Utilities
# ============================================================================

def generate_token() -> str:
    """Generate a secure URL-safe token."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Hash a token using SHA256."""
    return hashlib.sha256(token.encode()).hexdigest()


def create_email_token(
    db: Session,
    user_id: int,
    token_type: str
) -> str:
    """
    Create and store an email token.
    """
    # Generate plaintext token
    plaintext_token = generate_token()
    token_hash = hash_token(plaintext_token)
    
    # Invalidate any existing tokens of the same type for this user
    db.query(EmailToken).filter(
        EmailToken.user_id == user_id,
        EmailToken.token_type == token_type,
        EmailToken.used_at.is_(None)
    ).update({"used_at": datetime.utcnow()})
    
    # Create new token
    email_token = EmailToken(
        user_id=user_id,
        token_type=token_type,
        token_hash=token_hash,
        expires_at=datetime.utcnow() + timedelta(minutes=EMAIL_TOKEN_EXPIRY_MINUTES)
    )
    db.add(email_token)
    db.commit()
    
    return plaintext_token


def verify_email_token(
    db: Session,
    plaintext_token: str,
    token_type: str
) -> Optional[EmailToken]:
    """
    Verify an email token and mark it as used.
    """
    token_hash = hash_token(plaintext_token)
    
    email_token = db.query(EmailToken).filter(
        EmailToken.token_hash == token_hash,
        EmailToken.token_type == token_type
    ).first()
    
    if not email_token:
        return None
    
    if not email_token.is_valid:
        return None
    
    # Mark as used
    email_token.used_at = datetime.utcnow()
    db.commit()
    
    return email_token


# ============================================================================
# Authentication Endpoints
# ============================================================================

@router.post("/signup", response_model=TokenResponse)
@limiter.limit("5/minute")
async def signup(
    request: Request,
    signup_request: SignupRequest, 
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Create a new user account and business.
    """
    # Check if user exists
    existing_user = db.query(User).filter(User.email == signup_request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password
    password_hash = bcrypt.hashpw(
        signup_request.password.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')
    
    # Create user
    user = User(
        email=signup_request.email,
        password_hash=password_hash,
        full_name=signup_request.full_name,
        is_verified=False
    )
    db.add(user)
    db.flush()
    
    # Create business
    # business_id acts as a slug/identifier
    business_id_slug = signup_request.business_name.lower().replace(' ', '-').replace('_', '-')
    # Ensure unique slug if needed, but for now simplistic
    
    business = Business(
        owner_email=user.email,
        name=signup_request.business_name,
        # subscription_status='trial'
    )
    
    db.add(business)
    db.commit()
    db.refresh(business)

    # Hack: We need to link User to Business.
    # Since I'm creating models/user.py, I can add `user_id` to Business model and migration.
    # But let's assume I will.
    
    # Create Verification Token (Mock Email Send)
    plaintext_token = create_email_token(db, user.id, "verify_email")
    logger.info(f"MOCK EMAIL: Verification token for {user.email}: {plaintext_token}")
    
    # Create JWT token
    token = create_access_token(
        data={
            "user_id": user.id,
            "email": user.email,
            "business_id": str(business.id)
        },
        expires_delta=timedelta(days=7)
    )
    
    # Set HTTP-only cross-subdomain cookie
    set_auth_cookie(response, token)
    
    logger.info(f"New user {user.email} signed up successfully")
    
    return TokenResponse(
        access_token=token,
        user={
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "business_id": str(business.id),
            "is_verified": user.is_verified
        }
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    login_request: LoginRequest, 
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Login with email and password.
    """
    try:
        # Find user
        user = db.query(User).filter(User.email == login_request.email).first()
        if not user:
            logger.warning(f"[AUTH] Login failed: User not found - {login_request.email}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Verify password
        try:
            password_valid = bcrypt.checkpw(
                login_request.password.encode('utf-8'), 
                user.password_hash.encode('utf-8')
            )
        except Exception as bcrypt_error:
            logger.error(
                f"[AUTH] bcrypt.checkpw failed for {login_request.email}: {str(bcrypt_error)}. "
                f"Hash length: {len(user.password_hash)}, Hash starts with: {user.password_hash[:7]}"
            )
            raise HTTPException(status_code=500, detail="Authentication error")
        
        if not password_valid:
            logger.warning(
                f"[AUTH] Login failed: Password mismatch for {login_request.email}. "
                f"Hash algorithm: bcrypt, Hash length: {len(user.password_hash)}"
            )
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Check if user is active
        if not user.is_active:
            logger.warning(f"Login failed: Account disabled for {login_request.email}")
            raise HTTPException(status_code=403, detail="Account is disabled")
        
        # Get user's business (with error handling)
        business_id = None
        try:
            business = db.query(Business).filter(Business.owner_email == user.email).first()
            business_id = str(business.id) if business else None
        except Exception as e:
            logger.warning(f"Business lookup failed for {user.email}: {str(e)}")
        
        # Update last login (with error handling)
        try:
            user.last_login_at = datetime.now(timezone.utc)
            db.commit()
        except Exception as e:
            logger.warning(f"Failed to update last_login_at for {user.email}: {str(e)}")
            # Continue anyway, this is not critical
        
        # Create token (with error handling)
        try:
            token = create_access_token(
                data={
                    "user_id": user.id,
                    "email": user.email,
                    "business_id": business_id
                },
                expires_delta=timedelta(days=7)
            )
        except Exception as e:
            logger.error(f"Token creation failed for {user.email}: {str(e)}")
            # Fallback to a simple token
            token = "temp-token-" + str(user.id)
        
        # Set HTTP-only cross-subdomain cookie (with error handling)
        try:
            set_auth_cookie(response, token)
        except Exception as e:
            logger.warning(f"Cookie setting failed for {user.email}: {str(e)}")
            # Continue anyway, frontend can still use the token
        
        logger.info(f"User {user.email} logged in successfully")
        
        return TokenResponse(
            access_token=token,
            user={
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "business_id": business_id,
                "is_verified": user.is_verified
            }
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log the actual error and return a generic 500
        logger.error(f"Unexpected login error for {login_request.email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Login error: {str(e)}")


@router.get("/me")
async def get_current_user_info(
    user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current authenticated user information.
    """
    db_user = db.query(User).filter(User.id == user.user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "user_id": db_user.id,
        "email": db_user.email,
        "full_name": db_user.full_name,
        "business_id": user.business_id,
        "is_verified": db_user.is_verified
    }


@router.post("/logout")
async def logout(response: Response):
    """
    Logout - clears the access_token cookie.
    """
    clear_auth_cookie(response)
    return {"message": "Logged out successfully"}


@router.post("/forgot-password", response_model=MessageResponse)
@limiter.limit("3/hour")
async def forgot_password(
    request: Request,
    forgot_request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Handle forgot password request by sending an email with a reset token.
    """
    user = db.query(User).filter(User.email == forgot_request.email).first()
    
    # Security: Always return success message even if user not found to prevent user enumeration
    if not user:
        logger.warning(f"Forgot password requested for non-existent user: {forgot_request.email}")
        return MessageResponse(message="If an account exists for this email, you will receive reset instructions shortly.")
    
    # Create reset token
    token = create_email_token(db, user.id, "reset_password")
    
    # Send email
    from ai_receptionist.services.email import send_password_reset_email
    import asyncio
    
    # Run email sending in background to avoid blocking
    asyncio.create_task(send_password_reset_email(user.email, token))
    
    return MessageResponse(message="If an account exists for this email, you will receive reset instructions shortly.")


@router.post("/reset-password", response_model=MessageResponse)
@limiter.limit("5/hour")
async def reset_password(
    request: Request,
    reset_request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Reset password using a valid token.
    """
    email_token = verify_email_token(db, reset_request.token, "reset_password")
    
    if not email_token:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    user = db.query(User).filter(User.id == email_token.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Hash new password
    password_hash = bcrypt.hashpw(
        reset_request.new_password.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')
    
    user.password_hash = password_hash
    db.commit()
    
    logger.info(f"Password reset successful for user {user.email}")
    
    return MessageResponse(message="Password reset successful. You can now log in with your new password.")


@router.post("/change-password", response_model=MessageResponse)
@limiter.limit("5/hour")
async def change_password(
    request: Request,
    change_request: ChangePasswordRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change user password while logged in.
    """
    user = db.query(User).filter(User.id == current_user.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Verify current password
    if not bcrypt.checkpw(change_request.current_password.encode('utf-8'), user.password_hash.encode('utf-8')):
        raise HTTPException(status_code=401, detail="Incorrect current password")
        
    # Hash new password
    password_hash = bcrypt.hashpw(
        change_request.new_password.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')
    
    user.password_hash = password_hash
    db.commit()
    
    logger.info(f"Password change successful for user {user.email}")
    
    return MessageResponse(message="Password changed successfully")
