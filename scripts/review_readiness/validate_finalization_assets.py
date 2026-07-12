#!/usr/bin/env python3
"""Validate Review-Readiness finalization artifacts."""

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
        ROOT / "docs/review_readiness/mock-review-template.md",
        ROOT / "docs/review_readiness/rebuttal-prep-log.md",
        ROOT / "docs/review_readiness/repro-audit-report.md",
        ROOT / "docs/review_readiness/final-submission-checklist.md",
        ROOT / "docs/review_readiness/submission-bundle-manifest.md",
        ROOT / "docs/review_readiness/anonymized-release-checklist.md",
        ROOT / "output/corepaper_submission/corepaper_anonymous_release.zip",
    ]
    for f in files:
        require_file(f, errors)

    if errors:
        for e in errors:
            print(e, file=sys.stderr)
        return 1

    require_contains(ROOT / "docs/review_readiness/mock-review-template.md", ["## Consolidated Action Items"], errors)
    require_contains(ROOT / "docs/review_readiness/rebuttal-prep-log.md", ["| Issue ID | Reviewer Concern (Simulated) |"], errors)
    require_contains(ROOT / "docs/review_readiness/final-submission-checklist.md", ["PDF format and page budget fully compliant"], errors)
    require_contains(ROOT / "docs/review_readiness/repro-audit-report.md", ["## Fresh-Clone Reproduction Results", "| Artifact | Command |"], errors)
    require_contains(ROOT / "docs/review_readiness/anonymized-release-checklist.md", ["Review-Readiness-06", "anonymous_release.zip"], errors)

    if errors:
        for e in errors:
            print(e, file=sys.stderr)
        return 1

    print("Review-Readiness finalization assets validation successful.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
