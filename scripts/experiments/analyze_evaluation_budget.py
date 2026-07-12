#!/usr/bin/env python3
"""Summarize evaluation compute budget from suite logs."""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Dict, List


DEFAULT_SUITES = [
    "output/corepaper_logs/experiments/external_latest",
    "output/corepaper_logs/experiments/ablation_latest",
    "output/corepaper_logs/experiments/robustness_latest",
    "output/corepaper_logs/experiments/software_transfer_latest",
    "output/corepaper_logs/experiments/sim2sim_latest",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--suite-dirs",
        default=",".join(DEFAULT_SUITES),
        help="Comma-separated list of suite directories.",
    )
    parser.add_argument("--output-json", default="output/corepaper_reports/ws5/evaluation_budget.json")
    parser.add_argument("--output-md", default="output/corepaper_reports/ws5/evaluation_budget.md")
    return parser.parse_args()


def parse_suite_dirs(raw: str) -> List[pathlib.Path]:
    items = [it.strip() for it in raw.split(",") if it.strip()]
    if not items:
        raise ValueError("No suite dirs provided.")
    return [pathlib.Path(it) for it in items]


def mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def load_suite_row(suite_dir: pathlib.Path) -> Dict:
    summary_path = suite_dir / "suite_summary.json"
    if not summary_path.exists():
        raise FileNotFoundError(f"Missing summary: {summary_path}")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    durations: List[float] = []
    for path in sorted(suite_dir.glob("*.json")):
        if path.name == "suite_summary.json":
            continue
        row = json.loads(path.read_text(encoding="utf-8"))
        durations.append(float(row.get("duration_seconds", 0.0)))

    total_runs = int(summary.get("total_runs", len(durations)))
    total_duration = float(summary.get("duration_seconds", sum(durations)))
    return {
        "suite_name": summary.get("suite_name", suite_dir.name),
        "suite_dir": str(suite_dir),
        "total_runs": total_runs,
        "successful_runs": int(summary.get("successful_runs", total_runs)),
        "failed_runs": int(summary.get("failed_runs", 0)),
        "duration_seconds": round(total_duration, 3),
        "mean_run_seconds": round(mean(durations), 4),
        "runs_per_second": round((total_runs / total_duration), 3) if total_duration > 0 else 0.0,
    }


def markdown(payload: Dict) -> str:
    lines: List[str] = []
    lines.append("# Evaluation Budget Summary (Auto-generated)")
    lines.append("")
    lines.append(f"- Suites analyzed: {len(payload['suites'])}")
    lines.append(f"- Total runs: {payload['totals']['total_runs']}")
    lines.append(f"- Total wall-clock (s): {payload['totals']['duration_seconds']:.3f}")
    lines.append(f"- Aggregate throughput (runs/s): {payload['totals']['runs_per_second']:.3f}")
    lines.append("")
    lines.append("| Suite | Runs | Success | Failed | Wall-clock (s) | Mean run (s) | Throughput (runs/s) |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for row in payload["suites"]:
        lines.append(
            f"| {row['suite_name']} | {row['total_runs']} | {row['successful_runs']} | {row['failed_runs']} | "
            f"{row['duration_seconds']:.3f} | {row['mean_run_seconds']:.4f} | {row['runs_per_second']:.3f} |"
        )
    return "\n".join(lines).strip() + "\n"


def main() -> int:
    args = parse_args()
    suite_dirs = parse_suite_dirs(args.suite_dirs)
    rows = [load_suite_row(path) for path in suite_dirs]

    total_runs = sum(row["total_runs"] for row in rows)
    total_duration = sum(row["duration_seconds"] for row in rows)
    payload = {
        "suites": rows,
        "totals": {
            "total_runs": total_runs,
            "duration_seconds": round(total_duration, 3),
            "runs_per_second": round((total_runs / total_duration), 3) if total_duration > 0 else 0.0,
        },
    }

    out_json = pathlib.Path(args.output_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    out_md = pathlib.Path(args.output_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(markdown(payload), encoding="utf-8")

    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
