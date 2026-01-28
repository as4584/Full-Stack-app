from __future__ import annotations

import pytest

from ai_receptionist.services.router import IntentRouter, BookingStrategy, FAQStrategy, EscalationStrategy


@pytest.mark.parametrize(
    "intent,confidence,expected_cls",
    [
        ("book", 0.95, BookingStrategy),
        ("booking", 0.7, BookingStrategy),
        ("faq", 0.9, FAQStrategy),
        ("question", 0.8, FAQStrategy),
        ("unknown", 0.9, EscalationStrategy),
        ("book", 0.3, EscalationStrategy),  # low confidence fallback
        (None, 0.9, EscalationStrategy),
        ("", 0.9, EscalationStrategy),
    ],
)
def test_choose_strategy(intent, confidence, expected_cls):
    router = IntentRouter(threshold=0.6)
    strategy = router.choose_strategy(intent, confidence)
    assert isinstance(strategy, expected_cls)


def test_handle_actions_shape():
    router = IntentRouter(threshold=0.6)

    s1 = router.choose_strategy("book", 0.9)
    action1 = s1.handle(session={}, payload={})
    assert action1["type"] == "booking.start_flow"
    assert "missing" in action1

    s2 = router.choose_strategy("faq", 0.9)
    action2 = s2.handle(session={}, payload={"topic": "pricing"})
    assert action2["type"] == "faq.answer"
    assert action2["topic"] == "pricing"

    s3 = router.choose_strategy("unknown", 0.9)
    action3 = s3.handle(session={}, payload={"reason": "unsupported_intent"})
    assert action3["type"] == "escalate.human"
    assert action3["reason"] == "unsupported_intent"
