from datetime import datetime, timezone
from typing import List, Tuple, Dict, Any, Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import extract, func
from ai_receptionist.models.billing import BillingUsageEvent
from .billing import BillingRepository

class SqlAlchemyBillingRepository:
    """SQLAlchemy implementation of the BillingRepository protocol."""

    def __init__(self, session: Session):
        self.session = session

    def add_usage(self, tenant_id: str, minutes: int, ts: Optional[datetime] = None) -> None:
        if ts is None:
            ts = datetime.now(timezone.utc)
        
        event = BillingUsageEvent(
            business_id=int(tenant_id),
            minutes=minutes,
            created_at=ts
        )
        self.session.add(event)
        self.session.commit()

    def get_usage_for_month(self, tenant_id: str, year: int, month: int) -> List[Tuple[datetime, int]]:
        events = self.session.query(BillingUsageEvent).filter(
            BillingUsageEvent.business_id == int(tenant_id),
            extract('year', BillingUsageEvent.created_at) == year,
            extract('month', BillingUsageEvent.created_at) == month
        ).all()
        
        return [(e.created_at, e.minutes) for e in events]

    def get_rate_plan(self, tenant_id: str) -> Dict[str, Any]:
        # For now, return a default plan. In future, fetch from DB or Stripe.
        return {
            "mrc": Decimal("29.00"), 
            "rate_per_minute": Decimal("0.12"), 
            "currency": "usd"
        }
