#!/usr/bin/env python3
"""Validate WS1 literature asset completeness."""

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

    required_files = [
        ROOT / "docs/ws1/search-taxonomy.md",
        ROOT / "docs/ws1/retrieval-workflow.md",
        ROOT / "docs/ws1/coverage-matrix-template.md",
        ROOT / "docs/ws1/weekly-lit-brief-template.md",
        ROOT / "docs/ws1/claim-citation-matrix.md",
        ROOT / "docs/ws1/foundational-shortlist.md",
        ROOT / "docs/ws1/top-competitor-deep-review.md",
        ROOT / "scripts/literature/fetch_arxiv.py",
        ROOT / "scripts/literature/ingest_documents.py",
        ROOT / "scripts/literature/generate_weekly_delta.py",
        ROOT / "scripts/literature/build_coverage_matrix.py",
        ROOT / "scripts/literature/extract_structured_evidence.py",
        ROOT / "scripts/literature/generate_weekly_brief.py",
        ROOT / "output/corepaper_reports/literature/weekly_delta_latest.md",
        ROOT / "output/corepaper_reports/literature/coverage_matrix_latest.md",
        ROOT / "output/corepaper_reports/literature/evidence_table_latest.md",
        ROOT / "output/corepaper_reports/literature/weekly_brief_latest.md",
        ROOT / "data/papers/structured/evidence_latest.jsonl",
    ]
    for f in required_files:
        require_file(f, errors)

    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1

    require_contains(
        ROOT / "docs/ws1/retrieval-workflow.md",
        [
            "scripts/literature/fetch_arxiv.py",
            "scripts/literature/build_coverage_matrix.py",
            "scripts/literature/extract_structured_evidence.py",
            "scripts/literature/generate_weekly_brief.py",
        ],
        errors,
    )
    require_contains(
        ROOT / "docs/ws1/claim-citation-matrix.md",
        ["| Claim ID | Draft Claim |", "## Rules"],
        errors,
    )
    require_contains(
        ROOT / "docs/ws1/top-competitor-deep-review.md",
        ["| TC-01 |", "| TC-10 |", "Reviewer-Facing Summary"],
        errors,
    )

    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1

    print("WS1 literature assets validation successful.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
