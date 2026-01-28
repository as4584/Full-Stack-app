"""
Intent Router using the Strategy pattern.

Senior notes:
- Extend strategies by creating new classes implementing IntentStrategy.handle(session, payload) -> action.
- Register them in IntentRouter._intent_map or provide a hook to dynamically load from config.
- Confidence fallback: if confidence < threshold, route to EscalationStrategy to hand off to a human agent.
  Threshold can be tuned per-tenant or per-intent. Consider logging borderline cases for analysis.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional, Type


class IntentStrategy(ABC):
    """Strategy interface for intent handling.

    Single responsibility: given a session and payload, produce the next action.
    """

    @abstractmethod
    def handle(self, session: Mapping[str, Any], payload: Mapping[str, Any]) -> Dict[str, Any]:
        """Return an action dict, e.g., {"type": "booking.request_details", ...}."""
        raise NotImplementedError


class BookingStrategy(IntentStrategy):
    def handle(self, session: Mapping[str, Any], payload: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            "type": "booking.start_flow",
            "missing": [k for k in ("name", "service", "datetime") if not payload.get(k)],
        }


class FAQStrategy(IntentStrategy):
    def handle(self, session: Mapping[str, Any], payload: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            "type": "faq.answer",
            "topic": payload.get("topic") or "general",
        }


class EscalationStrategy(IntentStrategy):
    def handle(self, session: Mapping[str, Any], payload: Mapping[str, Any]) -> Dict[str, Any]:
        return {
            "type": "escalate.human",
            "reason": payload.get("reason") or "low_confidence_or_unknown_intent",
        }


@dataclass
class IntentRouter:
    """Routes intents to strategies based on intent label and confidence.

    Strategy pattern: choose_strategy returns a concrete IntentStrategy.
    Dependency inversion: callers depend on IntentStrategy interface, not concrete classes.
    """

    threshold: float = 0.6
    _intent_map: Optional[Dict[str, Type[IntentStrategy]]] = None

    def __post_init__(self) -> None:
        if self._intent_map is None:
            self._intent_map = {
                "book": BookingStrategy,
                "booking": BookingStrategy,
                "faq": FAQStrategy,
                "question": FAQStrategy,
            }

    def choose_strategy(self, intent: Optional[str], confidence: Optional[float]) -> IntentStrategy:
        # Fallback to escalation on low confidence or missing label
        if confidence is None or confidence < self.threshold:
            return EscalationStrategy()

        if not intent:
            return EscalationStrategy()

        key = intent.strip().lower()
        strategy_cls = self._intent_map.get(key) if self._intent_map else None
        if strategy_cls is None:
            return EscalationStrategy()
        return strategy_cls()
