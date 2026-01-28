from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Mapping


class TelephonyService(ABC):
    """Abstract interface for telephony operations.

    Single responsibility: define the telephony contract independent of vendor.
    """

    @abstractmethod
    def validate_signature(self, headers: Mapping[str, str], body: bytes, url: str | None = None) -> bool:
        """Validate webhook signature (easily mockable in unit tests)."""
        raise NotImplementedError

    @abstractmethod
    async def enqueue_call(self, event: Dict[str, Any]) -> None:
        """Enqueue an inbound call event (e.g., to Redis)."""
        raise NotImplementedError
