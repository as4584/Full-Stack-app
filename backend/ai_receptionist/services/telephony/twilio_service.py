from __future__ import annotations

import logging
from typing import Any, Dict, Mapping, Optional, List

from ai_receptionist.config.settings import Settings
from ai_receptionist.services.telephony.telephony import TelephonyService

logger = logging.getLogger(__name__)

try:  # Optional import to avoid hard dependency in tests
    from twilio.request_validator import RequestValidator
except Exception:  # pragma: no cover
    RequestValidator = None  # type: ignore

try:
    # Optional Redis support (prefer redis-py v5)
    from redis import asyncio as aioredis  # type: ignore
except Exception:  # pragma: no cover
    aioredis = None  # type: ignore


class TwilioTelephonyService(TelephonyService):
    """Twilio-based implementation of the TelephonyService.

    Single responsibility: adapt the generic telephony contract to Twilio specifics.
    """

    def __init__(self, settings: Settings, queue: Optional[List[Dict[str, Any]]] = None):
        self._settings = settings
        self._queue = queue  # Used in tests or simple local runs; production can use Redis client
        self._validator = None
        if RequestValidator and settings.twilio_auth_token:
            self._validator = RequestValidator(settings.twilio_auth_token)
        self._redis = None
        if aioredis and settings.redis_url:
            try:
                self._redis = aioredis.from_url(settings.redis_url, decode_responses=True)
            except Exception:
                self._redis = None

    def validate_signature(self, headers: Mapping[str, str], body: bytes, url: str | None = None) -> bool:
        """Validate Twilio signature.

        Note: Keep mockable for tests. In production, use twilio.request_validator.RequestValidator.
        """
        if not self._validator:
            return True  # fall back to permissive in dev/tests
        signature = headers.get("X-Twilio-Signature") or headers.get("x-twilio-signature")
        if not signature or not url:
            return False
        # Twilio sends form-encoded data typically; their validator expects dict of params
        try:
            from urllib.parse import parse_qsl

            params = dict(parse_qsl(body.decode("utf-8"))) if body else {}
        except Exception:
            params = {}
        try:
            return bool(self._validator.validate(url, params, signature))
        except Exception:
            return False

    async def enqueue_call(self, event: Dict[str, Any]) -> None:
        # Prefer Redis Stream if configured
        if self._redis is not None:
            try:
                await self._redis.xadd("calls", fields={k: str(v) for k, v in event.items()})
                return
            except Exception:
                pass
        if self._queue is not None:
            self._queue.append(event)
        # else: no-op in dev
