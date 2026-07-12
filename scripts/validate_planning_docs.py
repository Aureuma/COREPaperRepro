#!/usr/bin/env python3
"""Validate planning document integrity and required anchors."""

from __future__ import annotations

import pathlib
import sys


def main() -> int:
    root_dir = pathlib.Path(__file__).resolve().parents[1]

    required_files = [
        root_dir / "docs/plan.md",
    ]
    for file_path in required_files:
        if not file_path.is_file():
            print(f"Missing required file: {file_path}", file=sys.stderr)
            return 1

    required_patterns = [
        ("docs/plan.md", "## 9) Workstream Updates (Leave Space)"),
        ("docs/plan.md", "## 10) Work Item Updates (Leave Space)"),
        ("docs/plan.md", "## 13) Paper-Critique Response Plan (2026-02-18 to 2026-03-02)"),
        ("docs/plan.md", "### 13.2 Priority Work Packages (Critique-Driven)"),
        ("docs/plan.md", "| CR-01 | P0 |"),
        ("docs/plan.md", "| CR-17 | P2 |"),
        ("docs/plan.md", "### 13.6 2026-02-18 Evidence Pointers"),
        ("docs/plan.md", "## Source: `docs/ws0/compliance-checklist.md`"),
        ("docs/plan.md", "## Source: `docs/review_readiness/repro-audit-report.md`"),
    ]

    for rel_path, pattern in required_patterns:
        path = root_dir / rel_path
        if pattern not in path.read_text(encoding="utf-8"):
            print(f"Validation failed: '{pattern}' missing in {rel_path}", file=sys.stderr)
            return 1

    print("Planning docs validation successful.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
