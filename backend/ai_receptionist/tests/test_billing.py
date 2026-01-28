from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from ai_receptionist.services.billing import (
    BillingService,
    InMemoryBillingRepository,
    FakeStripeClient,
)


def test_billing_compute_and_invoice_simple_plan():
    # Arrange a simple rate plan: $100 MRC + $0.05 per minute
    repo = InMemoryBillingRepository(usage={}, plans={
        "tenant_1": {"mrc": Decimal("100.00"), "rate_per_minute": Decimal("0.05"), "currency": "usd"}
    })
    stripe = FakeStripeClient(created=[])
    svc = BillingService(repo=repo, stripe=stripe, stripe_customers={"tenant_1": "cus_123"})

    # Simulate usage: 200 minutes in current month
    now = datetime.now(timezone.utc)
    for _ in range(4):  # 4 events of 50 minutes
        repo.add_usage("tenant_1", 50, ts=now)

    # Act: compute the bill
    bill = svc.compute_monthly_bill("tenant_1", when=now)

    assert bill["total_minutes"] == 200
    assert bill["mrc"] == "100.00"
    assert bill["rate_per_minute"] == "0.05"
    # 200 * 0.05 = 10.00; total = 110.00
    assert bill["usage_cost"] == "10.00"
    assert bill["total"] == "110.00"

    # Act: create Stripe invoice
    inv = svc.create_invoice("tenant_1", when=now)

    assert inv["amount_cents"] == 11000
    assert inv["customer_id"] == "cus_123"
    assert stripe.created[-1]["amount_cents"] == 11000
    assert "invoice_id" in inv


def test_record_minutes_ignores_non_positive():
    repo = InMemoryBillingRepository(usage={}, plans={
        "t": {"mrc": Decimal("0.00"), "rate_per_minute": Decimal("0.10"), "currency": "usd"}
    })
    stripe = FakeStripeClient(created=[])
    svc = BillingService(repo=repo, stripe=stripe)

    svc.record_minutes("t", 0)
    svc.record_minutes("t", -5)
    assert repo.get_usage_for_month("t", datetime.now(timezone.utc).year, datetime.now(timezone.utc).month) == []
