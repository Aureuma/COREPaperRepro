#!/usr/bin/env python3
"""Generate a markdown dashboard from experiment run logs."""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Dict, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--logs-dir", default="output/corepaper_logs/experiments/latest")
    parser.add_argument("--output", default="output/corepaper_reports/experiments/regression_dashboard_latest.md")
    return parser.parse_args()


def load_run_reports(logs_dir: pathlib.Path) -> List[Dict]:
    runs: List[Dict] = []
    for path in sorted(logs_dir.glob("*.json")):
        if path.name == "suite_summary.json":
            continue
        runs.append(json.loads(path.read_text(encoding="utf-8")))
    return runs


def metric_value(report: Dict) -> str:
    payload = report.get("metric_payload", {})
    value = payload.get("primary_metric")
    if value is None:
        return ""
    return f"{float(value):.4f}"


def main() -> int:
    args = parse_args()
    logs_dir = pathlib.Path(args.logs_dir)
    output = pathlib.Path(args.output)

    runs = load_run_reports(logs_dir)
    lines: List[str] = []
    lines.append("# Regression Dashboard (Auto-generated)")
    lines.append("")
    lines.append(f"- Source logs: `{logs_dir}`")
    lines.append(f"- Total runs: {len(runs)}")
    lines.append("")
    lines.append("| Run ID | Return Code | Status | Primary Metric | Duration (s) |")
    lines.append("|---|---:|---|---:|---:|")
    for run in runs:
        lines.append(
            f"| {run.get('run_id','')} | {run.get('return_code','')} | "
            f"{'ok' if run.get('status_ok') else 'fail'} | {metric_value(run)} | "
            f"{float(run.get('duration_seconds', 0)):.3f} |"
        )
    if not runs:
        lines.append("| _none_ |  |  |  |  |")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    print(f"Regression dashboard written to: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

