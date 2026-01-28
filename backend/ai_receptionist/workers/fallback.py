from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Protocol

"""
Human fallback worker that consumes escalate events and persists them for human handling.

Design:
- Repository Pattern: FallbackRepository abstracts persistence (e.g., a Postgres table 'human_fallback').
- Dependency Injection: SlackNotifier is injected so tests can assert notifications without network calls.
- Queue Adapter: FallbackQueue abstracts the source of events (Redis, SQS, etc.). For tests we use an in-memory list.
"""


class FallbackRepository(Protocol):
    """Persistence port for human fallback entries."""

    def add_entry(self, tenant_id: str, caller: str, reason: str, raw: Dict[str, Any]) -> str:
        """Insert a new fallback entry and return its id."""
        ...


class SlackNotifier(Protocol):
    """Abstraction over Slack notification."""

    def notify(self, channel: str, text: str) -> None:
        ...


class FallbackQueue(Protocol):
    """Abstraction over an event queue with escalate events."""

    def pop(self) -> Optional[Dict[str, Any]]:
        ...


@dataclass
class InMemoryFallbackRepository:
    store: List[Dict[str, Any]]

    def add_entry(self, tenant_id: str, caller: str, reason: str, raw: Dict[str, Any]) -> str:
        entry_id = f"fb_{len(self.store) + 1}"
        self.store.append(
            {
                "id": entry_id,
                "tenant_id": tenant_id,
                "caller": caller,
                "reason": reason,
                "created_at": datetime.now(timezone.utc),
                "raw": raw,
            }
        )
        return entry_id


@dataclass
class InMemoryQueue:
    events: List[Dict[str, Any]]

    def pop(self) -> Optional[Dict[str, Any]]:
        if not self.events:
            return None
        return self.events.pop(0)


@dataclass
class FakeSlackNotifier:
    sent: List[Dict[str, str]]

    def notify(self, channel: str, text: str) -> None:
        self.sent.append({"channel": channel, "text": text})


class SlackWebhookNotifier:
    """Minimal Slack webhook notifier (sync wrapper around httpx)."""

    def __init__(self, webhook_url: str):
        self._webhook_url = webhook_url

    def notify(self, channel: str, text: str) -> None:
        try:
            import requests

            payload = {"text": f"[{channel}] {text}"}
            requests.post(self._webhook_url, json=payload, timeout=5)
        except Exception:
            # best-effort; do not raise in worker path
            pass


@dataclass
class FallbackWorker:
    repo: FallbackRepository
    notifier: SlackNotifier
    queue: FallbackQueue
    channel: str = "#human-fallback"

    def process_event(self, event: Dict[str, Any]) -> Optional[str]:
        """Process a single event; if flagged to escalate, persist and notify.

        Expected event fields:
        - type: should be 'escalate' or have 'escalate': True flag
        - tenant_id, caller, reason (optional)
        """
        escalate = event.get("type") == "escalate" or bool(event.get("escalate"))
        if not escalate:
            return None

        tenant_id = event.get("tenant_id") or "unknown"
        caller = event.get("caller") or "unknown"
        reason = event.get("reason") or "unspecified"

        entry_id = self.repo.add_entry(tenant_id=tenant_id, caller=caller, reason=reason, raw=event)
        text = f"Escalation for tenant={tenant_id} caller={caller} reason={reason} entry_id={entry_id}"
        self.notifier.notify(self.channel, text)
        return entry_id

    async def run_once(self) -> int:
        """Pop and process a single event if available; return 1 if processed else 0."""
        ev = self.queue.pop()
        if not ev:
            return 0
        self.process_event(ev)
        return 1
