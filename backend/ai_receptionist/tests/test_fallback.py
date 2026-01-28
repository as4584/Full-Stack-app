from __future__ import annotations

from workers.fallback import (
    InMemoryFallbackRepository,
    FakeSlackNotifier,
    FallbackWorker,
    InMemoryQueue,
)


def test_escalate_event_persists_and_notifies():
    repo = InMemoryFallbackRepository(store=[])
    notifier = FakeSlackNotifier(sent=[])
    queue = InMemoryQueue(events=[])

    worker = FallbackWorker(repo=repo, notifier=notifier, queue=queue)

    event = {
        "type": "escalate",
        "tenant_id": "tenant_123",
        "caller": "+15551234567",
        "reason": "customer_requested_human",
        "context": {"last_intent": "escalation"},
    }

    entry_id = worker.process_event(event)

    assert entry_id is not None
    assert len(repo.store) == 1
    saved = repo.store[0]
    assert saved["tenant_id"] == "tenant_123"
    assert saved["caller"] == "+15551234567"
    assert saved["reason"] == "customer_requested_human"
    assert "created_at" in saved

    assert len(notifier.sent) == 1
    note = notifier.sent[0]
    assert note["channel"] == "#human-fallback"
    assert "tenant_123" in note["text"]
    assert entry_id in note["text"]


def test_non_escalate_event_is_ignored():
    repo = InMemoryFallbackRepository(store=[])
    notifier = FakeSlackNotifier(sent=[])
    queue = InMemoryQueue(events=[])

    worker = FallbackWorker(repo=repo, notifier=notifier, queue=queue)

    event = {"type": "info", "tenant_id": "t", "caller": "c"}
    result = worker.process_event(event)

    assert result is None
    assert repo.store == []
    assert notifier.sent == []
