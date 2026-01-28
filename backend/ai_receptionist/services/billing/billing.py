from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Protocol, List, Dict, Any, Optional, Tuple

"""
Billing service with metered usage and Stripe invoice creation.

Design notes:
- Repository Pattern: BillingRepository abstracts persistence (e.g., Postgres).
- Dependency Injection: Stripe client is injected so tests can mock network calls.
- Metered billing: minutes are recorded as discrete usage events and billed at a per-minute rate
  plus a monthly recurring charge (MRC). Consider soft/hard caps to avoid surprise costs.
- Rounding: currency math uses Decimal; cents are computed by quantizing to 2 decimals.
"""


class BillingRepository(Protocol):
    """Persistence port for billing data (e.g., Postgres).

    In a real implementation, this would use an async DB client and proper schemas.
    """

    def add_usage(self, tenant_id: str, minutes: int, ts: Optional[datetime] = None) -> None:
        ...

    def get_usage_for_month(self, tenant_id: str, year: int, month: int) -> List[Tuple[datetime, int]]:
        ...

    def get_rate_plan(self, tenant_id: str) -> Dict[str, Any]:
        """Return plan config: { 'mrc': Decimal, 'rate_per_minute': Decimal, 'currency': 'usd' }"""
        ...


@dataclass
class InMemoryBillingRepository:
    """Simple in-memory repository used for tests and local runs."""

    # usage events keyed by tenant: list of (timestamp, minutes)
    usage: Dict[str, List[Tuple[datetime, int]]]
    # rate plans keyed by tenant
    plans: Dict[str, Dict[str, Any]]

    def add_usage(self, tenant_id: str, minutes: int, ts: Optional[datetime] = None) -> None:
        ts = ts or datetime.now(timezone.utc)
        self.usage.setdefault(tenant_id, []).append((ts, minutes))

    def get_usage_for_month(self, tenant_id: str, year: int, month: int) -> List[Tuple[datetime, int]]:
        events = self.usage.get(tenant_id, [])
        return [
            (ts, mins)
            for (ts, mins) in events
            if ts.year == year and ts.month == month
        ]

    def get_rate_plan(self, tenant_id: str) -> Dict[str, Any]:
        return self.plans.get(
            tenant_id,
            {"mrc": Decimal("0.00"), "rate_per_minute": Decimal("0.00"), "currency": "usd"},
        )


class StripeClient(Protocol):
    """Abstraction over Stripe for DI and testability."""

    def create_invoice(self, customer_id: str, amount_cents: int, description: str) -> str:
        ...


@dataclass
class FakeStripeClient:
    """Test double capturing invoice creation calls."""

    created: List[Dict[str, Any]]

    def create_invoice(self, customer_id: str, amount_cents: int, description: str) -> str:
        invoice_id = f"test_inv_{len(self.created) + 1}"
        self.created.append(
            {
                "invoice_id": invoice_id,
                "customer_id": customer_id,
                "amount_cents": amount_cents,
                "description": description,
            }
        )
        return invoice_id


@dataclass
class BillingService:
    repo: BillingRepository
    stripe: StripeClient
    # Optional map tenant_id -> stripe_customer_id for tests/demo
    stripe_customers: Dict[str, str] | None = None

    def record_minutes(self, tenant_id: str, minutes: int) -> None:
        if minutes <= 0:
            return
        self.repo.add_usage(tenant_id, minutes)

    def compute_monthly_bill(self, tenant_id: str, when: Optional[datetime] = None) -> Dict[str, Any]:
        when = when or datetime.now(timezone.utc)
        plan = self.repo.get_rate_plan(tenant_id)
        mrc: Decimal = plan.get("mrc", Decimal("0.00"))
        rate: Decimal = plan.get("rate_per_minute", Decimal("0.00"))
        currency: str = plan.get("currency", "usd")

        events = self.repo.get_usage_for_month(tenant_id, when.year, when.month)
        total_minutes = sum(mins for _, mins in events)

        usage_cost = (rate * Decimal(total_minutes)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total = (mrc + usage_cost).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return {
            "tenant_id": tenant_id,
            "year": when.year,
            "month": when.month,
            "currency": currency,
            "total_minutes": total_minutes,
            "mrc": str(mrc),
            "rate_per_minute": str(rate),
            "usage_cost": str(usage_cost),
            "total": str(total),
        }

    def create_invoice(self, tenant_id: str, when: Optional[datetime] = None) -> Dict[str, Any]:
        bill = self.compute_monthly_bill(tenant_id, when=when)
        amount_decimal = Decimal(bill["total"])  # already quantized to 2 decimals
        amount_cents = int((amount_decimal * Decimal("100")).to_integral_value(rounding=ROUND_HALF_UP))

        # In a real app, lookup stripe customer id from DB/config
        customer_id = None
        if self.stripe_customers:
            customer_id = self.stripe_customers.get(tenant_id)
        customer_id = customer_id or f"customer_{tenant_id}"

        description = f"AI Receptionist monthly invoice {bill['year']}-{bill['month']:02d}"
        invoice_id = self.stripe.create_invoice(customer_id=customer_id, amount_cents=amount_cents, description=description)
        return {
            "invoice_id": invoice_id,
            "amount_cents": amount_cents,
            "currency": bill["currency"],
            "customer_id": customer_id,
            "breakdown": bill,
        }
