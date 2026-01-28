from typing import Dict, Optional
import logging

from ai_receptionist.config.settings import Settings, get_settings
from ai_receptionist.services.telephony.telephony import TelephonyService
from ai_receptionist.services.telephony.twilio_service import TwilioTelephonyService
from ai_receptionist.services.flags.service import FeatureFlagService, FeatureFlagRepository, RedisLike

logger = logging.getLogger(__name__)


def get_telephony_service(settings: Settings | None = None) -> TelephonyService:
    """Dependency provider returning a TelephonyService interface instance.

    Uses dependency inversion: API depends on TelephonyService interface, not concrete Twilio service.
    """
    s = settings or get_settings()
    return TwilioTelephonyService(settings=s)


def get_tenant_mapping() -> Dict[str, str]:
    """Provide a phone-number-to-tenant_id mapping.

    In production, this could come from a database or settings. Overridden in tests.
    """
    return {}


# --- Feature flags wiring ---

class _InMemoryFlagsRepo(FeatureFlagRepository):
    def __init__(self):
        self._plan_by_tenant: Dict[str, str] = {}
        # Example defaults per plan
        self._plan_flags: Dict[str, Dict[str, bool]] = {
            "starter": {"allow_rag": False, "allow_ai_booking": False},
            "core": {"allow_rag": True, "allow_ai_booking": True},
            "pro": {"allow_rag": True, "allow_ai_booking": True},
            "enterprise": {"allow_rag": True, "allow_ai_booking": True},
        }
        self._overrides: Dict[str, Dict[str, bool]] = {}

    def get_tenant_plan(self, tenant_id: str) -> str:
        return self._plan_by_tenant.get(tenant_id, "starter")

    def get_plan_flags(self, plan_slug: str) -> Dict[str, bool]:
        return self._plan_flags.get(plan_slug, {})

    def get_tenant_overrides(self, tenant_id: str) -> Dict[str, bool]:
        return self._overrides.get(tenant_id, {})

    def set_tenant_flag(self, tenant_id: str, flag_name: str, enabled: bool, admin_user: str) -> None:
        self._overrides.setdefault(tenant_id, {})[flag_name] = bool(enabled)

    def set_tenant_plan(self, tenant_id: str, plan_slug: str, admin_user: str) -> None:
        self._plan_by_tenant[tenant_id] = plan_slug


class _InMemoryRedis(RedisLike):
    def __init__(self):
        self.store: Dict[str, str] = {}

    def get(self, key: str) -> Optional[str]:
        return self.store.get(key)

    def setex(self, key: str, ttl_seconds: int, value: str) -> None:
        self.store[key] = value

    def delete(self, key: str) -> None:
        self.store.pop(key, None)


_FLAGS_REPO = _InMemoryFlagsRepo()
_FLAGS_CACHE = _InMemoryRedis()


def get_feature_flag_service() -> FeatureFlagService:
    # Defaults can be extended here
    default_flags = {"allow_rag": False, "allow_ai_booking": False}
    return FeatureFlagService(repo=_FLAGS_REPO, redis=_FLAGS_CACHE, default_flags=default_flags)
