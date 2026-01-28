from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, Optional, Protocol


CACHE_TTL_SECONDS = 30


class RedisLike(Protocol):
    def get(self, key: str) -> Optional[bytes | str]:
        ...

    def setex(self, key: str, ttl_seconds: int, value: str) -> None:
        ...

    def delete(self, key: str) -> None:
        ...


class FeatureFlagRepository(Protocol):
    def get_tenant_plan(self, tenant_id: str) -> str:
        ...

    def get_plan_flags(self, plan_slug: str) -> Dict[str, bool]:
        ...

    def get_tenant_overrides(self, tenant_id: str) -> Dict[str, bool]:
        ...

    def set_tenant_flag(self, tenant_id: str, flag_name: str, enabled: bool, admin_user: str) -> None:
        ...

    def set_tenant_plan(self, tenant_id: str, plan_slug: str, admin_user: str) -> None:
        ...


def _cache_key(tenant_id: str) -> str:
    return f"tenant:flags:{tenant_id}"


@dataclass
class FeatureFlagService:
    repo: FeatureFlagRepository
    redis: RedisLike
    default_flags: Dict[str, bool]

    def get_effective_flags(self, tenant_id: str) -> Dict[str, bool]:
        key = _cache_key(tenant_id)
        cached = self.redis.get(key)
        if cached:
            try:
                if isinstance(cached, bytes):
                    cached = cached.decode("utf-8")
                return json.loads(cached)  # type: ignore[arg-type]
            except Exception:
                # On cache parse failure, drop through to rebuild
                pass

        plan = self.repo.get_tenant_plan(tenant_id)
        plan_flags = self.repo.get_plan_flags(plan)
        overrides = self.repo.get_tenant_overrides(tenant_id)

        effective = {**self.default_flags, **plan_flags, **overrides}
        self.redis.setex(key, CACHE_TTL_SECONDS, json.dumps(effective, separators=(",", ":")))
        return effective

    def invalidate(self, tenant_id: str) -> None:
        self.redis.delete(_cache_key(tenant_id))

    def set_tenant_flag(self, tenant_id: str, flag_name: str, enabled: bool, admin_user: str) -> Dict[str, bool]:
        self.repo.set_tenant_flag(tenant_id, flag_name, enabled, admin_user)
        self.invalidate(tenant_id)
        return self.get_effective_flags(tenant_id)

    def set_tenant_plan(self, tenant_id: str, plan_slug: str, admin_user: str) -> Dict[str, bool]:
        self.repo.set_tenant_plan(tenant_id, plan_slug, admin_user)
        self.invalidate(tenant_id)
        return self.get_effective_flags(tenant_id)
