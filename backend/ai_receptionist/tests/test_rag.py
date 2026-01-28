from __future__ import annotations

from typing import Any, Dict, List

import pytest

from services import rag


class FakeVectorStore(rag.VectorStore):
    def __init__(self, docs: List[Dict[str, Any]]):
        self.docs = docs

    def query(self, tenant_id: str, text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        # ignore text and top_k for simplicity in this test
        return self.docs


@pytest.fixture(autouse=True)
def patch_vector_store(monkeypatch):
    # Provide a fake global vector store used by generate_prompt
    docs = [
        {"text": "FAQ: We offer cuts and color."},
        {"text": "Policy: 24-hour cancellation required."},
    ]
    monkeypatch.setattr(rag, "VECTOR_STORE", FakeVectorStore(docs))


def test_generate_prompt_includes_tenant_and_rules():
    session_context = {
        "tenant_config": {
            "tenant_name": "Acme Salon",
            "hours": "Mon-Fri 9-5, Sat 10-4",
            "cancellation_policy": "24-hour notice required",
            "top_faqs": ["Walk-ins accepted", "Gift cards available"],
            "booking_rules": "Require full name and phone number to book.",
        }
    }

    prompt = rag.generate_prompt(
        tenant_id="tenant_123",
        user_text="I'd like to book a haircut",
        session_context=session_context,
    )

    assert "Acme Salon" in prompt
    assert "Require full name and phone number to book." in prompt
    # Retrieved docs should show up
    assert "FAQ: We offer cuts and color." in prompt
    assert "24-hour cancellation" in prompt
