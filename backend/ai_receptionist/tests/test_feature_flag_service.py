from __future__ import annotations

import json
from typing import Dict


from ai_receptionist.services.flags.service import FeatureFlagService, FeatureFlagRepository, RedisLike, CACHE_TTL_SECONDS


class FakeRedis(RedisLike):
    def __init__(self):
        self.store: Dict[str, str] = {}
        self.set_calls: list[tuple[str, int, str]] = []
        self.deleted: list[str] = []

    def get(self, key: str):
        return self.store.get(key)

    def setex(self, key: str, ttl_seconds: int, value: str) -> None:
        self.set_calls.append((key, ttl_seconds, value))
        self.store[key] = value

    def delete(self, key: str) -> None:
        self.deleted.append(key)
        self.store.pop(key, None)


class FakeRepo(FeatureFlagRepository):
    def __init__(self, plan_by_tenant: Dict[str, str], plan_flags: Dict[str, Dict[str, bool]], overrides: Dict[str, Dict[str, bool]]):
        self.plan_by_tenant = plan_by_tenant
        self.plan_flags = plan_flags
        self.overrides = overrides
        self.calls: Dict[str, int] = {"get_plan": 0, "get_flags": 0, "get_overrides": 0, "set_flag": 0, "set_plan": 0}

    def get_tenant_plan(self, tenant_id: str) -> str:
        self.calls["get_plan"] += 1
        return self.plan_by_tenant.get(tenant_id, "starter")

    def get_plan_flags(self, plan_slug: str) -> Dict[str, bool]:
        self.calls["get_flags"] += 1
        return self.plan_flags.get(plan_slug, {})

    def get_tenant_overrides(self, tenant_id: str) -> Dict[str, bool]:
        self.calls["get_overrides"] += 1
        return self.overrides.get(tenant_id, {})

    def set_tenant_flag(self, tenant_id: str, flag_name: str, enabled: bool, admin_user: str) -> None:
        self.calls["set_flag"] += 1
        self.overrides.setdefault(tenant_id, {})[flag_name] = bool(enabled)

    def set_tenant_plan(self, tenant_id: str, plan_slug: str, admin_user: str) -> None:
        self.calls["set_plan"] += 1
        self.plan_by_tenant[tenant_id] = plan_slug


def test_get_effective_flags_uses_cache_when_present():
    redis = FakeRedis()
    repo = FakeRepo({"t1": "core"}, {"core": {"allow_ai_booking": True}}, {"t1": {"allow_rag": True}})
    svc = FeatureFlagService(repo=repo, redis=redis, default_flags={"allow_rag": False, "allow_ai_booking": False})

    # Prime cache
    cached = {"allow_rag": True, "allow_ai_booking": True}
    redis.store["tenant:flags:t1"] = json.dumps(cached)

    flags = svc.get_effective_flags("t1")
    assert flags == cached
    # Repo should not be consulted when cache hit
    assert repo.calls["get_plan"] == 0
    assert repo.calls["get_flags"] == 0
    assert repo.calls["get_overrides"] == 0


def test_get_effective_flags_builds_and_caches():
    redis = FakeRedis()
    repo = FakeRepo({"t2": "core"}, {"core": {"allow_ai_booking": True}}, {"t2": {"allow_rag": True}})
    svc = FeatureFlagService(repo=repo, redis=redis, default_flags={"allow_rag": False, "allow_ai_booking": False})

    flags = svc.get_effective_flags("t2")
    assert flags == {"allow_rag": True, "allow_ai_booking": True}
    # Cached with TTL
    assert redis.set_calls, "expected a setex call"
    key, ttl, value = redis.set_calls[-1]
    assert key == "tenant:flags:t2"
    assert ttl == CACHE_TTL_SECONDS
    assert json.loads(value) == flags


def test_set_tenant_flag_updates_and_invalidates():
    redis = FakeRedis()
    # Pre-cache something to ensure invalidate path is exercised
    redis.store["tenant:flags:t3"] = json.dumps({"allow_rag": False})

    repo = FakeRepo({"t3": "starter"}, {"starter": {"allow_ai_booking": False}}, {"t3": {}})
    svc = FeatureFlagService(repo=repo, redis=redis, default_flags={"allow_rag": False, "allow_ai_booking": False})

    flags = svc.set_tenant_flag("t3", "allow_rag", True, admin_user="lex")
    assert repo.calls["set_flag"] == 1
    # Cache invalidated and then recomputed
    assert "tenant:flags:t3" in redis.deleted
    assert flags["allow_rag"] is True


def test_set_tenant_plan_updates_and_invalidates():
    redis = FakeRedis()
    repo = FakeRepo({"t4": "starter"}, {"starter": {"allow_ai_booking": False}, "core": {"allow_ai_booking": True}}, {"t4": {}})
    svc = FeatureFlagService(repo=repo, redis=redis, default_flags={"allow_rag": False, "allow_ai_booking": False})

    flags = svc.set_tenant_plan("t4", "core", admin_user="lex")
    assert repo.calls["set_plan"] == 1
    assert flags["allow_ai_booking"] is True
