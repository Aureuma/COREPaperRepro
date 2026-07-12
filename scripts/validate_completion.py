#!/usr/bin/env python3
"""Validate end-to-end completion criteria for repository-implemented work items."""

from __future__ import annotations

import pathlib
import sys
from typing import List


ROOT = pathlib.Path(__file__).resolve().parents[1]


def read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def require_file(path: pathlib.Path, errors: List[str]) -> None:
    if not path.is_file():
        errors.append(f"Missing file: {path}")
        return
    if path.stat().st_size == 0:
        errors.append(f"Empty file: {path}")


def require_contains(path: pathlib.Path, pattern: str, errors: List[str]) -> None:
    content = read(path)
    if pattern not in content:
        errors.append(f"Missing pattern '{pattern}' in {path}")


def main() -> int:
    errors: List[str] = []

    required = [
        ROOT / "docs/acceptance-criteria.md",
        ROOT / "docs/plan.md",
        ROOT / "output/corepaper_reports/literature/weekly_brief_latest.md",
        ROOT / "output/corepaper_reports/literature/evidence_table_latest.md",
        ROOT / "output/corepaper_reports/literature/coverage_matrix_latest.md",
        ROOT / "output/corepaper_reports/experiments/summary_latest.md",
        ROOT / "output/corepaper_reports/experiments/regression_dashboard_latest.md",
        ROOT / "output/corepaper_reports/experiments/integrity_report_latest.json",
        ROOT / "output/corepaper_reports/ws3/external_baseline_summary.md",
        ROOT / "output/corepaper_reports/ws3/baseline_calibration.md",
        ROOT / "output/corepaper_reports/ws5/ablation_results.md",
        ROOT / "output/corepaper_reports/ws5/robustness_results.md",
        ROOT / "output/corepaper_reports/ws5/software_transfer_results.md",
        ROOT / "output/corepaper_reports/ws5/sim2sim_transfer_results.md",
        ROOT / "output/corepaper_reports/ws5/statistical_effects.md",
        ROOT / "paper/figures/metaworld_taskwise.pdf",
        ROOT / "paper/figures/custom_diagnostics.pdf",
        ROOT / "paper/figures/uncertainty_dominance.pdf",
        ROOT / "paper/figures/gate_timeline.pdf",
        ROOT / "output/corepaper_assets/video/manifest.json",
        ROOT / "output/corepaper_assets/video/comparisons/S1-hard.mp4",
        ROOT / "output/corepaper_assets/video/comparisons/S2-med.mp4",
        ROOT / "output/corepaper_assets/video/comparisons/S3-severe.mp4",
        ROOT / "output/corepaper_assets/video/comparisons/SIM-isaac.mp4",
        ROOT / "output/corepaper_submission/corepaper_main_paper_draft.pdf",
        ROOT / "output/corepaper_submission/corepaper_video.mp4",
        ROOT / "output/corepaper_submission/corepaper_anonymous_release.zip",
        ROOT / "output/corepaper_submission/corepaper_submission_bundle.zip",
        ROOT / "docs/review_readiness/repro-audit-report.md",
        ROOT / "docs/ws5/sim2sim-validation-log.md",
        ROOT / "docs/ws3/baseline-calibration-note.md",
        ROOT / "docs/review_readiness/anonymized-release-checklist.md",
        ROOT / "docs/ws8/video-storyboard.md",
        ROOT / "docs/ws8/media-production-log.md",
        ROOT / "site/index.html",
    ]
    for path in required:
        require_file(path, errors)

    if errors:
        for e in errors:
            print(e, file=sys.stderr)
        return 1

    plan_text = read(ROOT / "docs/plan.md")
    if "| Not Started |" in plan_text:
        errors.append("Plan still contains 'Not Started' statuses.")
    if "| In Progress |" in plan_text:
        errors.append("Plan still contains 'In Progress' statuses.")
    if " | Done |" not in plan_text:
        errors.append("Plan does not contain any completed status rows.")

    require_contains(ROOT / "docs/ws6/claim-evidence-matrix.md", "| C1 |", errors)
    require_contains(ROOT / "docs/review_readiness/mock-review-template.md", "Overall score:", errors)
    require_contains(ROOT / "docs/ws5/failure-taxonomy.md", "| F-01 |", errors)

    cycles = sorted((ROOT / "output/corepaper_logs/ws4/cycles").glob("*.json"))
    if len(cycles) < 3:
        errors.append("Expected at least 3 WS4 cycle logs.")

    if errors:
        for e in errors:
            print(e, file=sys.stderr)
        return 1

    print("Completion criteria validation successful.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
