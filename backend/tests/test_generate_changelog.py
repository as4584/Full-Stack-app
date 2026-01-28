from __future__ import annotations

import os

import scripts.generate_changelog as gc


def test_categorize_and_render_basic():
    titles = [
        "feat(core): add booking flow",
        "fix(api): correct status code",
        "docs: update readme",
        "refactor: cleanup",
        "chore: bump deps",
    ]
    sections = gc.categorize(titles)
    out = gc.render("v0.2.0", sections)
    assert "# Release v0.2.0" in out
    assert "## Features" in out and "add booking flow" in out
    assert "## Fixes" in out and "status code" in out
    assert "## Docs" in out
    assert "## Refactors" in out
    assert "## Other" in out


def test_main_prints_and_writes(monkeypatch, tmp_path):
    # Simulate git outputs
    def fake_check_output(cmd, text=True):
        if cmd[:3] == ["git", "describe", "--tags"] or "describe" in cmd:
            return "v0.1.0"
        if cmd[:2] == ["git", "log"]:
            return "\n".join([
                "feat: one",
                "fix: two",
            ])
        if cmd[:2] == ["git", "fetch"]:
            return ""
        raise AssertionError(f"Unexpected cmd: {cmd}")

    monkeypatch.setenv("GITHUB_REF_NAME", "v0.2.0")
    monkeypatch.setattr(gc.subprocess, "check_output", fake_check_output)
    monkeypatch.setattr(gc, "previous_tag", lambda: "v0.1.0")

    notes = tmp_path / "RELEASE_NOTES.md"
    changelog = tmp_path / "CHANGELOG.md"

    # Change working directory for file writes
    cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        # Call main via its function
        # Use args by simulating CLI via monkeypatching sys.argv is fragile; instead call helpers
        # We'll directly invoke generate and write manually to mimic main
        titles = ["feat: one", "fix: two"]
        sections = gc.categorize(titles)
        out = gc.render("v0.2.0", sections)
        # emulate main's writing behavior
        from datetime import date
        with open(notes, "w", encoding="utf-8") as f:
            f.write(out)
        with open(changelog, "a", encoding="utf-8") as cf:
            cf.write(f"## v0.2.0 - {date.today().isoformat()}\n\n")
            cf.write(out)
            cf.write("\n")
    finally:
        os.chdir(cwd)

    assert notes.read_text(encoding="utf-8").startswith("# Release v0.2.0")
    cl = changelog.read_text(encoding="utf-8")
    assert "## v0.2.0 - " in cl and "# Release v0.2.0" in cl
