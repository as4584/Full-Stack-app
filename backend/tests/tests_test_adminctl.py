from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from click.testing import CliRunner

import tools.adminctl as adminctl


class DummyResponse:
    def __init__(self, status_code: int, json_data: Dict[str, Any] | None = None, text: str = ""):
        self.status_code = status_code
        self._json = json_data
        self.text = text

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300

    def json(self) -> Dict[str, Any]:
        if self._json is None:
            raise ValueError("No JSON")
        return self._json


def _write_env(tmp_home: Path) -> None:
    envp = tmp_home / ".adminctl.env"
    envp.write_text("ADMIN_PRIVATE_KEY=secret-key\n", encoding="utf-8")


def test_set_plan_makes_put_request(monkeypatch, tmp_path):
    tmp_home = tmp_path / "home"
    tmp_home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HOME", str(tmp_home))
    _write_env(tmp_home)

    captured = {}

    def fake_request(method, url, headers=None, json=None, timeout=10):  # noqa: A002
        captured["method"] = method
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        return DummyResponse(200, json_data={"ok": True, "plan": json["plan"]})

    monkeypatch.setattr(adminctl.requests, "request", fake_request)

    runner = CliRunner()
    result = runner.invoke(adminctl.adminctl, [
        "set-plan",
        "--tenant", "t1",
        "--plan", "core",
        "--admin-user", "lex",
    ])

    assert result.exit_code == 0, result.output
    assert captured["method"] == "PUT"
    assert captured["url"].endswith("/admin/tenants/t1/plan")
    assert captured["json"] == {"plan": "core"}
    auth = captured["headers"].get("Authorization", "")
    assert auth.startswith("Bearer ")


def test_set_flag_puts_enable_boolean(monkeypatch, tmp_path):
    tmp_home = tmp_path / "home"
    tmp_home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HOME", str(tmp_home))
    _write_env(tmp_home)

    captured = {}

    def fake_request(method, url, headers=None, json=None, timeout=10):  # noqa: A002
        captured["method"] = method
        captured["url"] = url
        captured["json"] = json
        return DummyResponse(200, json_data={"ok": True})

    monkeypatch.setattr(adminctl.requests, "request", fake_request)

    runner = CliRunner()
    result = runner.invoke(adminctl.adminctl, [
        "set-flag",
        "--tenant", "t1",
        "--flag", "allow_rag",
        "--enable", "true",
        "--admin-user", "lex",
    ])

    assert result.exit_code == 0, result.output
    assert captured["method"] == "PUT"
    assert captured["url"].endswith("/admin/tenants/t1/flags/allow_rag")
    assert captured["json"] == {"enable": True}


def test_show_flags_gets_json_and_prints(monkeypatch, tmp_path):
    tmp_home = tmp_path / "home"
    tmp_home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HOME", str(tmp_home))
    _write_env(tmp_home)

    def fake_request(method, url, headers=None, json=None, timeout=10):  # noqa: A002
        return DummyResponse(200, json_data={"allow_rag": True, "allow_ai_booking": False})

    monkeypatch.setattr(adminctl.requests, "request", fake_request)

    runner = CliRunner()
    result = runner.invoke(adminctl.adminctl, [
        "show-flags",
        "--tenant", "t2",
    ])

    assert result.exit_code == 0, result.output
    out = result.output.strip()
    parsed = json.loads(out)
    assert parsed == {"allow_ai_booking": False, "allow_rag": True}
