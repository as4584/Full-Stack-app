from __future__ import annotations

import os
from typing import Dict

import jwt
from fastapi import APIRouter, Depends, Header, HTTPException

from ai_receptionist.core.di import get_feature_flag_service
from ai_receptionist.services.flags.service import FeatureFlagService


router = APIRouter(prefix="/admin", tags=["admin"])


def _verify_admin_jwt(authorization: str | None = Header(default=None)) -> Dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")
    token = authorization.split(" ", 1)[1]
    key = os.environ.get("ADMIN_PRIVATE_KEY")
    if not key:
        # Allow Settings-based keys if desired in future; env keeps it simple
        raise HTTPException(status_code=500, detail="admin key not configured")
    try:
        payload = jwt.decode(token, key, algorithms=["HS256"])
        if payload.get("scope") != "admin":
            raise HTTPException(status_code=403, detail="forbidden")
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="invalid token")


@router.put("/tenants/{tenant_id}/plan")
def set_plan(tenant_id: str, body: Dict[str, str], svc: FeatureFlagService = Depends(get_feature_flag_service), _: Dict = Depends(_verify_admin_jwt)):
    plan = (body or {}).get("plan")
    if not plan:
        raise HTTPException(status_code=422, detail="plan is required")
    flags = svc.set_tenant_plan(tenant_id, plan, admin_user="api")
    return {"ok": True, "tenant": tenant_id, "plan": plan, "flags": flags}


@router.put("/tenants/{tenant_id}/flags/{flag}")
def set_flag(tenant_id: str, flag: str, body: Dict[str, bool], svc: FeatureFlagService = Depends(get_feature_flag_service), _: Dict = Depends(_verify_admin_jwt)):
    enable = bool((body or {}).get("enable"))
    flags = svc.set_tenant_flag(tenant_id, flag, enable, admin_user="api")
    return {"ok": True, "tenant": tenant_id, "flag": flag, "enable": enable, "flags": flags}


@router.get("/tenants/{tenant_id}/flags")
def show_flags(tenant_id: str, svc: FeatureFlagService = Depends(get_feature_flag_service), _: Dict = Depends(_verify_admin_jwt)):
    return svc.get_effective_flags(tenant_id)
