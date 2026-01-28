from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class Call(Base):
    """
    Records a phone call processed by the AI receptionist.
    """
    __tablename__ = "calls"

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    call_sid = Column(String(50), unique=True, index=True)
    from_number = Column(String(50))
    to_number = Column(String(50))
    status = Column(String(50), default="in-progress") # in-progress, completed, failed
    duration = Column(Integer, default=0) # duration in seconds
    transcript = Column(Text, nullable=True)
    recording_url = Column(String(255), nullable=True)
    summary = Column(Text, nullable=True)
    intent = Column(String(255), nullable=True) # Overall intent of the call
    appointment_booked = Column(Integer, default=0) # 1 if an appointment was booked
    
    # Conversation Frame for Shadow AI & Testing (Sync only structured data)
    # Stores: List[Turn] {role, text, metadata {intent, tools, latency, ts}}
    conversation_frame = Column(Text, nullable=True) # JSON stored as Text or JSON type
    shadow_result = Column(Text, nullable=True) # JSON comparison result
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    business = relationship("Business", backref="calls")

    def __repr__(self):
        return f"<Call(sid='{self.call_sid}', from='{self.from_number}', status='{self.status}')>"
