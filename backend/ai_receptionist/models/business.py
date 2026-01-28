from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Text, JSON, Boolean
from .base import Base

class Business(Base):
    """
    Business profile and AI persona settings.
    """
    __tablename__ = "businesses"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    owner_email = Column(String(255), index=True) # Link to User
    name = Column(String(255), nullable=False)
    industry = Column(String(255))
    description = Column(Text)
    phone_number = Column(String(50))
    is_active = Column(Integer, default=1) # 1 = Active, 0 = Inactive
    receptionist_enabled = Column(Boolean, default=True, server_default='1')
    phone_number_sid = Column(String(50)) # Twilio SID for the purchased number
    phone_number_status = Column(String(50), default="pending") # pending, active, cancelled
    
    # AI Persona
    greeting_style = Column(String(50), default="professional")
    business_hours = Column(String(255))
    common_services = Column(Text)
    timezone = Column(String(100), default="America/New_York")
    
    # Knowledge Base
    faqs = Column(JSON, default=[]) # List of {question, answer}

    # Billing & Stripe
    stripe_customer_id = Column(String(255), nullable=True)
    subscription_status = Column(String(50), default="active") # active, past_due, canceled
    
    # Usage Limits
    minutes_used = Column(Integer, default=0)
    minutes_limit = Column(Integer, default=100)
    billing_cycle_start = Column(DateTime, default=datetime.utcnow)
    
    # Simulation / Auditor (RAG 2.0)
    pending_description = Column(Text, nullable=True)
    pending_faqs = Column(JSON, nullable=True)
    audit_status = Column(String(50), default="verified") # verified, pending, rejected
    audit_report = Column(JSON, nullable=True)

    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Business(name='{self.name}', phone='{self.phone_number}')>"
