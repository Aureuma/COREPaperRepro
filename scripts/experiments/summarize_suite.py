#!/usr/bin/env python3
"""Summarize experiment suite metrics with group means and confidence intervals."""

from __future__ import annotations

import argparse
import json
import math
import pathlib
from typing import Dict, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--logs-dir", default="output/corepaper_logs/experiments/latest")
    parser.add_argument("--output-json", default="output/corepaper_reports/experiments/summary_latest.json")
    parser.add_argument("--output-md", default="output/corepaper_reports/experiments/summary_latest.md")
    return parser.parse_args()


def mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def std(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = mean(values)
    var = sum((v - m) ** 2 for v in values) / (len(values) - 1)
    return math.sqrt(var)


def ci95(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    # Normal approximation for lightweight reporting.
    return 1.96 * std(values) / math.sqrt(len(values))


def group_name(run_id: str) -> str:
    if "-" in run_id:
        return run_id.split("-", 1)[0]
    return run_id


def load_runs(logs_dir: pathlib.Path) -> List[Dict]:
    rows: List[Dict] = []
    for path in sorted(logs_dir.glob("*.json")):
        if path.name == "suite_summary.json":
            continue
        rows.append(json.loads(path.read_text(encoding="utf-8")))
    return rows


def main() -> int:
    args = parse_args()
    logs_dir = pathlib.Path(args.logs_dir)
    runs = load_runs(logs_dir)

    grouped: Dict[str, List[float]] = {}
    for run in runs:
        payload = run.get("metric_payload", {}) or {}
        metric = payload.get("primary_metric")
        if metric is None:
            continue
        g = group_name(str(run.get("run_id", "")))
        grouped.setdefault(g, []).append(float(metric))

    summary_rows: List[Dict] = []
    for g, values in sorted(grouped.items()):
        summary_rows.append(
            {
                "group": g,
                "n": len(values),
                "mean": mean(values),
                "std": std(values),
                "ci95": ci95(values),
            }
        )

    out_json = pathlib.Path(args.output_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps({"groups": summary_rows}, indent=2) + "\n", encoding="utf-8")

    lines: List[str] = []
    lines.append("# Experiment Summary (Auto-generated)")
    lines.append("")
    lines.append(f"- Source logs: `{logs_dir}`")
    lines.append(f"- Total runs: {len(runs)}")
    lines.append("")
    lines.append("| Group | N | Mean | Std | 95% CI |")
    lines.append("|---|---:|---:|---:|---:|")
    for row in summary_rows:
        lines.append(
            f"| {row['group']} | {row['n']} | {row['mean']:.4f} | {row['std']:.4f} | {row['ci95']:.4f} |"
        )
    if not summary_rows:
        lines.append("| _none_ | 0 | 0 | 0 | 0 |")

    out_md = pathlib.Path(args.output_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")

    print(f"Experiment summary JSON written to: {out_json}")
    print(f"Experiment summary markdown written to: {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

