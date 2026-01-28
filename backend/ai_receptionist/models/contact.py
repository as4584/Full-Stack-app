from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    phone_number = Column(String(50), nullable=False, index=True)
    
    name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    
    is_blocked = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    business = relationship("Business")

    def __repr__(self):
        return f"<Contact(phone='{self.phone_number}', name='{self.name}')>"
