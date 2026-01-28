from sqlalchemy import Column, Integer, String, DateTime, Float, JSON
from datetime import datetime
from .base import Base

class EvaluationBenchmark(Base):
    """
    Stores aggregate performance metrics for the AI Receptionist.
    Tracks booking success rate, average turns, p95 latency, etc.
    """
    __tablename__ = "evaluation_benchmarks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    version = Column(String(50), index=True) # AI Model version or Prompt version
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    total_calls = Column(Integer, default=0)
    booking_success_rate = Column(Float, default=0.0)
    avg_turns_per_booking = Column(Float, default=0.0)
    false_confirmations = Column(Integer, default=0)
    p95_latency_ms = Column(Float, default=0.0)
    
    # Store detailed distribution or comparison stats
    raw_data = Column(JSON, nullable=True)

    def __repr__(self):
        return f"<EvaluationBenchmark(version='{self.version}', success_rate={self.booking_success_rate})>"
