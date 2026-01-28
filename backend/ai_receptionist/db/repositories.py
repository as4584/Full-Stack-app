from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class ReceptionLogRepository(Protocol):
    """Port for persisting reception events/logs."""

    def save_event(self, event: dict) -> None:
        ...


@dataclass
class InMemoryReceptionLogRepository:
    """Simple in-memory repository for demo/testing."""

    store: list[dict]

    def save_event(self, event: dict) -> None:
        self.store.append(event)
