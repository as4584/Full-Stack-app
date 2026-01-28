from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import click
import jwt
import requests


ENV_FILE = os.path.expanduser("~/.adminctl.env")


def _read_env_file(path: str) -> Dict[str, str]:
    env: Dict[str, str] = {}
    if not os.path.exists(path):
        return env
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def _make_token(admin_user: str, tenant: Optional[str], private_key: str, ttl_seconds: int = 60) -> str:
    now = int(time.time())
    payload = {
        "iss": "adminctl",
        "sub": admin_user,
        "scope": "admin",
        "iat": now,
        "exp": now + ttl_seconds,
    }
    if tenant:
        payload["tenant_id"] = tenant
    return jwt.encode(payload, private_key, algorithm="HS256")


@dataclass
class Client:
    base_url: str
    admin_user: str
    private_key: str

    def _headers(self, tenant: Optional[str]) -> Dict[str, str]:
        token = _make_token(self.admin_user, tenant, self.private_key)
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    def request(self, method: str, path: str, *, tenant: Optional[str] = None, json_body: Optional[Dict[str, Any]] = None) -> requests.Response:
        url = self.base_url.rstrip("/") + path
        headers = self._headers(tenant)
        return requests.request(method, url, headers=headers, json=json_body, timeout=10)


def _get_client(admin_user: str) -> Client:
    env = _read_env_file(ENV_FILE)
    private_key = env.get("ADMIN_PRIVATE_KEY") or os.environ.get("ADMIN_PRIVATE_KEY")
    if not private_key:
        click.echo("Missing ADMIN_PRIVATE_KEY in ~/.adminctl.env or environment", err=True)
        sys.exit(2)
    base_url = os.environ.get("ADMIN_API_URL", "http://localhost:8080")
    return Client(base_url=base_url, admin_user=admin_user, private_key=private_key)


@click.group()
def adminctl():
    """Admin CLI for tenant plans and flags."""


@adminctl.command("set-plan")
@click.option("--tenant", required=True, help="Tenant ID")
@click.option("--plan", required=True, type=click.Choice(["starter", "core", "pro", "enterprise"], case_sensitive=False))
@click.option("--admin-user", required=True, help="Admin user name")
def set_plan(tenant: str, plan: str, admin_user: str):
    client = _get_client(admin_user)
    resp = client.request("PUT", f"/admin/tenants/{tenant}/plan", tenant=tenant, json_body={"plan": plan.lower()})
    click.echo(resp.text if resp.text else "")
    if not resp.ok:
        sys.exit(1)


@adminctl.command("set-flag")
@click.option("--tenant", required=True, help="Tenant ID")
@click.option("--flag", required=True, help="Flag name")
@click.option("--enable", required=True, type=bool, help="Enable (true/false)")
@click.option("--admin-user", required=True, help="Admin user name")
def set_flag(tenant: str, flag: str, enable: bool, admin_user: str):
    client = _get_client(admin_user)
    resp = client.request("PUT", f"/admin/tenants/{tenant}/flags/{flag}", tenant=tenant, json_body={"enable": bool(enable)})
    click.echo(resp.text if resp.text else "")
    if not resp.ok:
        sys.exit(1)


@adminctl.command("show-flags")
@click.option("--tenant", required=True, help="Tenant ID")
@click.option("--admin-user", required=False, default="system", help="Admin user name")
def show_flags(tenant: str, admin_user: str):
    client = _get_client(admin_user)
    resp = client.request("GET", f"/admin/tenants/{tenant}/flags", tenant=tenant)
    if resp.ok:
        try:
            data = resp.json()
        except Exception:
            data = {"raw": resp.text}
        click.echo(json.dumps(data, indent=2, sort_keys=True))
    else:
        click.echo(resp.text if resp.text else "")
        sys.exit(1)


if __name__ == "__main__":
    adminctl()
