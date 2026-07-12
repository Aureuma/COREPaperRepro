#!/usr/bin/env python3
"""Validate core WS2/WS3 planning artifacts."""

from __future__ import annotations

import json
import pathlib
import sys
from typing import Dict, List


ROOT = pathlib.Path(__file__).resolve().parents[1]


def require_file(path: pathlib.Path, errors: List[str]) -> None:
    if not path.is_file():
        errors.append(f"Missing required file: {path}")


def require_contains(path: pathlib.Path, snippets: List[str], errors: List[str]) -> None:
    content = path.read_text(encoding="utf-8")
    for snippet in snippets:
        if snippet not in content:
            errors.append(f"Missing snippet in {path}: {snippet}")


def validate_manifest(path: pathlib.Path, errors: List[str]) -> None:
    payload: Dict = json.loads(path.read_text(encoding="utf-8"))
    for key in ("project", "tasks", "baselines", "metrics", "evaluation_policy"):
        if key not in payload:
            errors.append(f"config/benchmark_manifest.json missing key: {key}")
    if not isinstance(payload.get("tasks", []), list) or not payload.get("tasks"):
        errors.append("config/benchmark_manifest.json requires at least one task entry")
    if not isinstance(payload.get("baselines", []), list) or not payload.get("baselines"):
        errors.append("config/benchmark_manifest.json requires at least one baseline entry")


def main() -> int:
    errors: List[str] = []

    files = [
        ROOT / "docs/ws2/problem-brief.md",
        ROOT / "docs/ws2/hypothesis-ledger.md",
        ROOT / "docs/ws2/theory-experiment-matrix.md",
        ROOT / "docs/ws2/theory-note-v1.md",
        ROOT / "docs/ws2/contingency-hypotheses.md",
        ROOT / "docs/ws3/benchmark-protocol.md",
        ROOT / "config/benchmark_manifest.json",
    ]
    for file in files:
        require_file(file, errors)

    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1

    require_contains(
        ROOT / "docs/ws2/hypothesis-ledger.md",
        ["| Hypothesis ID |", "| H1 |", "## Update Rules"],
        errors,
    )
    require_contains(
        ROOT / "docs/ws3/benchmark-protocol.md",
        ["## Baseline Set", "## Metrics", "## Fairness Controls", "## Statistical Plan"],
        errors,
    )
    require_contains(
        ROOT / "docs/ws2/theory-note-v1.md",
        ["## Assumptions", "## Core Analytical Claims", "## Derivation Checklist"],
        errors,
    )
    require_contains(
        ROOT / "docs/ws2/contingency-hypotheses.md",
        ["| Contingency ID | Trigger Condition | Alternative Hypothesis |", "## Decision Rules"],
        errors,
    )
    validate_manifest(ROOT / "config/benchmark_manifest.json", errors)

    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1

    print("Research protocol validation successful.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
