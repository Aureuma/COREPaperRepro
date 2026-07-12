#!/usr/bin/env python3
"""Validate WS5 evaluation assets."""

from __future__ import annotations

import pathlib
import sys
from typing import List


ROOT = pathlib.Path(__file__).resolve().parents[2]


def require_file(path: pathlib.Path, errors: List[str]) -> None:
    if not path.is_file():
        errors.append(f"Missing file: {path}")


def require_contains(path: pathlib.Path, snippets: List[str], errors: List[str]) -> None:
    content = path.read_text(encoding="utf-8")
    for snippet in snippets:
        if snippet not in content:
            errors.append(f"Missing snippet in {path}: {snippet}")


def main() -> int:
    errors: List[str] = []
    files = [
        ROOT / "docs/ws5/main-results-template.md",
        ROOT / "docs/ws5/ablation-plan.md",
        ROOT / "docs/ws5/robustness-suite.md",
        ROOT / "docs/ws5/software-validation-log.md",
        ROOT / "docs/ws5/sim2sim-validation-log.md",
        ROOT / "docs/ws5/practicality-template.md",
        ROOT / "docs/ws5/statistical-validation-plan.md",
        ROOT / "docs/ws5/failure-taxonomy.md",
        ROOT / "output/corepaper_reports/ws5/ablation_results.md",
        ROOT / "output/corepaper_reports/ws5/robustness_results.md",
        ROOT / "output/corepaper_reports/ws5/software_transfer_results.md",
        ROOT / "output/corepaper_reports/ws5/sim2sim_transfer_results.md",
        ROOT / "output/corepaper_reports/ws5/statistical_effects.md",
    ]
    for f in files:
        require_file(f, errors)

    if errors:
        for e in errors:
            print(e, file=sys.stderr)
        return 1

    require_contains(ROOT / "docs/ws5/main-results-template.md", ["| Method | Primary Metric |"], errors)
    require_contains(ROOT / "docs/ws5/ablation-plan.md", ["| Ablation ID |", "## Rules"], errors)
    require_contains(ROOT / "docs/ws5/robustness-suite.md", ["| Test ID | Disturbance Type |"], errors)
    require_contains(ROOT / "docs/ws5/software-validation-log.md", ["| Slice ID |", "| SW-01 |"], errors)
    require_contains(ROOT / "docs/ws5/sim2sim-validation-log.md", ["| S2S-01 |", "Source engine"], errors)
    require_contains(ROOT / "docs/ws5/failure-taxonomy.md", ["| Failure ID | Scenario |"], errors)

    if errors:
        for e in errors:
            print(e, file=sys.stderr)
        return 1

    print("WS5 evaluation assets validation successful.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
