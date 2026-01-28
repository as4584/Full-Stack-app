"""
RAG (Retrieval-Augmented Generation) helpers for assembling prompts.

Design patterns:
- Adapter: VectorStore is an abstraction; ConcreteVectorStore adapts Pinecone to this interface.
- Template Method: PromptTemplate defines the structure of the prompt, with tenant config and retrieved snippets.

This module keeps Pinecone import optional so unit tests can run without the dependency.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol


class VectorStore(Protocol):
    """Adapter interface for vector retrieval backends.

    Single Responsibility: expose retrieval by tenant namespace.
    """

    def query(self, tenant_id: str, text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        ...


class NoopVectorStore:
    """Fallback store used when no backend is configured."""

    def query(self, tenant_id: str, text: str, top_k: int = 5) -> List[Dict[str, Any]]:  # noqa: D401
        return []


@dataclass
class ConcreteVectorStore:
    """Pinecone-backed VectorStore (optional dependency).

    The Pinecone client is lazily imported to keep tests lightweight and mockable.
    """

    index_name: str
    api_key: Optional[str] = None

    def _client(self):
        try:
            # Pinecone SDK v5 (example): from pinecone import Pinecone
            from pinecone import Pinecone  # type: ignore

            return Pinecone(api_key=self.api_key) if self.api_key else Pinecone()
        except Exception:  # pragma: no cover - optional dependency not installed in tests
            return None

    def query(self, tenant_id: str, text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        pc = self._client()
        if pc is None:  # Fallback when pinecone isn't available
            return []

        try:  # Example interaction; adjust to actual SDK in real implementation
            index = pc.Index(self.index_name)
            # Namespace scoping ensures tenant isolation
            res = index.query(
                vector=text,  # In reality, you'd embed the text first; this is a placeholder
                top_k=top_k,
                namespace=tenant_id,
                include_metadata=True,
            )
            # Normalize to a list of dicts with 'text'
            out: List[Dict[str, Any]] = []
            for match in getattr(res, "matches", []) or []:
                md = getattr(match, "metadata", {}) or {}
                text_val = md.get("text") or md.get("content") or ""
                out.append({"text": text_val})
            return out
        except Exception:
            return []

    @classmethod
    def from_env(cls) -> "ConcreteVectorStore":
        import os

        return cls(index_name=os.getenv("PINECONE_INDEX", "receptionist-index"), api_key=os.getenv("PINECONE_API_KEY"))


class PromptTemplate:
    """Template Method for assembling the prompt text."""

    def build(self, tenant_config: Dict[str, Any], user_text: str, retrieved: List[Dict[str, Any]]) -> str:
        header = self._build_header(tenant_config)
        guidance = self._build_guidance(tenant_config)
        context = self._build_context(retrieved)
        return f"{header}\n\n{guidance}\n\nUser: {user_text}\n\nContext:\n{context}\n"

    def _build_header(self, tenant_config: Dict[str, Any]) -> str:
        tenant_name = tenant_config.get("tenant_name", "Unknown Tenant")
        hours = tenant_config.get("hours", "")
        policy = tenant_config.get("cancellation_policy", "")
        top_faqs = tenant_config.get("top_faqs", [])
        faqs_str = "\n- ".join(top_faqs) if top_faqs else ""
        return (
            f"You are the AI receptionist for {tenant_name}.\n"
            f"Business hours: {hours}.\n"
            f"Cancellation policy: {policy}.\n"
            + (f"Top FAQs:\n- {faqs_str}\n" if faqs_str else "")
        )

    def _build_guidance(self, tenant_config: Dict[str, Any]) -> str:
        booking_rules = tenant_config.get("booking_rules", "")
        return (
            "Follow these booking rules strictly.\n"
            f"Booking rules: {booking_rules}"
        )

    def _build_context(self, retrieved: List[Dict[str, Any]]) -> str:
        if not retrieved:
            return "(no additional context)"
        lines = [f"- {d.get('text', '')}" for d in retrieved if d.get("text")]
        return "\n".join(lines)


# Default vector store can be replaced/mocked in tests
VECTOR_STORE: VectorStore = NoopVectorStore()


def generate_prompt(tenant_id: str, user_text: str, session_context: Dict[str, Any]) -> str:
    """Generate a system prompt for the AI receptionist.

    - Uses Adapter pattern to retrieve tenant-scoped relevant context via VectorStore
    - Uses Template Method pattern to assemble the final prompt
    """
    tenant_config = session_context.get("tenant_config", {})

    # Retrieve tenant-scoped documents
    retrieved = VECTOR_STORE.query(tenant_id=tenant_id, text=user_text, top_k=5)

    # Build prompt
    template = PromptTemplate()
    prompt = template.build(tenant_config=tenant_config, user_text=user_text, retrieved=retrieved)
    return prompt
