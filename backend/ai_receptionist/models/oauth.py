"""
Database models for OAuth token storage.
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Text, Boolean
from .base import Base


class GoogleOAuthToken(Base):
    """
    Stores encrypted Google OAuth tokens for calendar integration.
    
    Each record represents a tenant's connected Google Calendar account.
    """
    __tablename__ = "google_oauth_tokens"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Encrypted tokens
    access_token_encrypted = Column(Text, nullable=False)
    refresh_token_encrypted = Column(Text, nullable=False)
    
    # Token metadata
    token_type = Column(String(50), nullable=False, default="Bearer")
    expires_at = Column(DateTime, nullable=False)
    scope = Column(Text, nullable=False)
    
    # Connection status
    is_connected = Column(Boolean, nullable=False, default=True)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<GoogleOAuthToken(tenant_id='{self.tenant_id}', connected={self.is_connected})>"
