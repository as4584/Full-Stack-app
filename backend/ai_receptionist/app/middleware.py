from __future__ import annotations

import logging
import uuid
from typing import Callable

from fastapi import Request


try:
    # Python 3.11+ contextvars already present in stdlib
    import contextvars
except Exception:  # pragma: no cover - fallback shouldn't trigger
    contextvars = None  # type: ignore


request_id_var = (contextvars.ContextVar("request_id") if contextvars else None)  # type: ignore
tenant_id_var = (contextvars.ContextVar("tenant_id") if contextvars else None)  # type: ignore


class _ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:  # noqa: D401
        """Inject request_id and tenant_id into log records when available."""
        if request_id_var:
            try:
                record.request_id = request_id_var.get()  # type: ignore[attr-defined]
            except LookupError:
                record.request_id = "-"  # type: ignore[attr-defined]
        else:
            record.request_id = "-"  # type: ignore[attr-defined]
        if tenant_id_var:
            try:
                record.tenant_id = tenant_id_var.get()  # type: ignore[attr-defined]
            except LookupError:
                record.tenant_id = "-"  # type: ignore[attr-defined]
        else:
            record.tenant_id = "-"  # type: ignore[attr-defined]
        return True


def configure_logging() -> None:
    """Attach a formatter that includes tenant_id and request_id if not already configured."""
    logger = logging.getLogger()
    if not any(isinstance(f, _ContextFilter) for f in logger.filters):
        logger.addFilter(_ContextFilter())
    if not logger.handlers:
        handler = logging.StreamHandler()
        fmt = "%(asctime)s %(levelname)s %(name)s: %(message)s"
        handler.setFormatter(logging.Formatter(fmt))
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)


async def request_context_middleware(request: Request, call_next: Callable):
    """FastAPI middleware to attach request_id and tenant_id to context and request.state."""
    rid = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    tid = request.headers.get("X-Tenant-ID") or request.query_params.get("tenant_id") or "-"

    if request_id_var:
        request_id_var.set(rid)
    if tenant_id_var:
        tenant_id_var.set(tid)

    # Also available on request.state
    request.state.request_id = rid
    request.state.tenant_id = tid

    response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    return response
