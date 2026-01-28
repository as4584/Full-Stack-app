#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from collections import defaultdict
from typing import Dict, List


def run(cmd: List[str]) -> str:
    return subprocess.check_output(cmd, text=True).strip()


def previous_tag() -> str | None:
    try:
        # previous annotated/lightweight tag before HEAD
        return run(["git", "describe", "--tags", "--abbrev=0", "HEAD^"])
    except Exception:
        return None


def commit_titles(rng: str) -> List[str]:
    try:
        out = run(["git", "log", "--pretty=%s", rng])
        return [line for line in out.split("\n") if line.strip()]
    except Exception:
        return []


def categorize(titles: List[str]) -> Dict[str, List[str]]:
    sections: Dict[str, List[str]] = defaultdict(list)
    for t in titles:
        key = "other"
        lower = t.lower()
        if lower.startswith("feat"):
            key = "features"
        elif lower.startswith("fix"):
            key = "fixes"
        elif lower.startswith("docs"):
            key = "docs"
        elif lower.startswith("refactor"):
            key = "refactors"
        elif lower.startswith("perf"):
            key = "performance"
        elif lower.startswith("test"):
            key = "tests"
        sections[key].append(t)
    return sections


def render(version: str, sections: Dict[str, List[str]]) -> str:
    order = ["features", "fixes", "docs", "refactors", "performance", "tests", "other"]
    lines = [f"# Release {version}", ""]
    for sec in order:
        items = sections.get(sec)
        if not items:
            continue
        lines.append(f"## {sec.capitalize()}")
        for i in items:
            lines.append(f"- {i}")
        lines.append("")
    if len(lines) == 2:
        lines.append("No notable changes.")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="from_tag", default=None, help="Start tag (optional)")
    ap.add_argument("--to", dest="to_ref", default="HEAD", help="End ref (default HEAD)")
    ap.add_argument("--output", dest="output", default="-", help="Output file or - for stdout")
    ap.add_argument("--changelog", dest="changelog", default="CHANGELOG.md", help="Changelog file to append to")
    args = ap.parse_args()

    version = os.environ.get("GITHUB_REF_NAME", "Unreleased")
    try:
        subprocess.check_call(["git", "fetch", "--tags"])  # ensure tags present in CI
    except Exception:
        pass

    start = args.from_tag or previous_tag()
    rng = f"{start}..{args.to_ref}" if start else args.to_ref
    titles = commit_titles(rng)
    sections = categorize(titles)
    out = render(version, sections)

    # Always print the generated release notes
    sys.stdout.write(out)

    # Optionally write to a separate output file (e.g., RELEASE_NOTES.md)
    if args.output != "-":
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out)

    # Append an entry to CHANGELOG.md with version and date
    from datetime import date

    header = f"## {version} - {date.today().isoformat()}\n\n"
    try:
        with open(args.changelog, "a", encoding="utf-8") as cf:
            cf.write(header)
            cf.write(out)
            cf.write("\n")
    except Exception:
        # Best-effort; do not fail the release on changelog write
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
