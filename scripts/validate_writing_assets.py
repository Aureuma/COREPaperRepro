#!/usr/bin/env python3
"""Validate WS6 writing scaffold artifacts."""

from __future__ import annotations

import pathlib
import sys
from typing import List


ROOT = pathlib.Path(__file__).resolve().parents[1]


def check_exists(path: pathlib.Path, errors: List[str]) -> None:
    if not path.is_file():
        errors.append(f"Missing required file: {path}")


def check_contains(path: pathlib.Path, required_snippets: List[str], errors: List[str]) -> None:
    content = path.read_text(encoding="utf-8")
    for snippet in required_snippets:
        if snippet not in content:
            errors.append(f"Missing snippet in {path}: {snippet}")


def main() -> int:
    errors: List[str] = []

    paper = ROOT / "docs/ws6/paper-skeleton.md"
    claims = ROOT / "docs/ws6/claim-evidence-matrix.md"
    figures = ROOT / "docs/ws6/figure-plan.md"
    positioning = ROOT / "docs/ws6/positioning-memo.md"
    limitations = ROOT / "docs/ws6/limitations-ethics.md"
    final_checklist = ROOT / "docs/ws6/final-edit-checklist.md"
    framing_memo = ROOT / "docs/ws6/framing-correction-memo.md"
    figure_integrity = ROOT / "docs/ws6/figure-integrity-checklist.md"

    for f in (paper, claims, figures, positioning, limitations, final_checklist, framing_memo, figure_integrity):
        check_exists(f, errors)

    if errors:
        for e in errors:
            print(e, file=sys.stderr)
        return 1

    check_contains(
        paper,
        [
            "## 1. Introduction",
            "## 2. Related Work",
            "## 3. Method",
            "## 4. Experimental Setup",
            "## 5. Results",
            "## 6. Discussion and Limitations",
            "## 7. Conclusion",
        ],
        errors,
    )
    check_contains(claims, ["| Claim ID |", "No manuscript claim is allowed"], errors)
    check_contains(figures, ["| Figure ID |", "| F1 |", "| F5 |"], errors)
    check_contains(positioning, ["## Closest Competing Papers", "## Overclaim Guardrails"], errors)
    check_contains(limitations, ["## Limitations", "## Safety Considerations", "## Ethical Considerations"], errors)
    check_contains(final_checklist, ["## Clarity", "## Evidence Consistency", "## Compliance and Presentation"], errors)
    check_contains(framing_memo, ["Algorithm-Centric Framing Memo", "Framing Corrections Applied"], errors)
    check_contains(figure_integrity, ["Figure Integrity Checklist", "| Main benchmark bars |"], errors)

    if errors:
        for e in errors:
            print(e, file=sys.stderr)
        return 1

    print("WS6 writing assets validation successful.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
