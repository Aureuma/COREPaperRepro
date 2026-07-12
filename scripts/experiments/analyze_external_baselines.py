#!/usr/bin/env python3
"""Analyze external baseline suite outputs and generate WS3 report."""

from __future__ import annotations

import argparse
import json
import math
import pathlib
from typing import Dict, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--logs-dir", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-md", required=True)
    return parser.parse_args()


def mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def std(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = mean(values)
    return math.sqrt(sum((v - m) ** 2 for v in values) / (len(values) - 1))


def ci95(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    return 1.96 * std(values) / math.sqrt(len(values))


def group_from_run_id(run_id: str) -> str:
    if "-s" in run_id:
        return run_id.rsplit("-s", 1)[0]
    return run_id


def load_runs(path: pathlib.Path) -> List[Dict]:
    rows: List[Dict] = []
    for f in sorted(path.glob("*.json")):
        if f.name == "suite_summary.json":
            continue
        rows.append(json.loads(f.read_text(encoding="utf-8")))
    return rows


def main() -> int:
    args = parse_args()
    runs = load_runs(pathlib.Path(args.logs_dir))
    grouped: Dict[str, List[float]] = {}
    for run in runs:
        run_id = str(run.get("run_id", ""))
        val = run.get("metric_payload", {}).get("primary_metric")
        if val is None:
            continue
        grouped.setdefault(group_from_run_id(run_id), []).append(float(val))

    rows = []
    for group, vals in grouped.items():
        rows.append(
            {
                "group": group,
                "n": len(vals),
                "mean": mean(vals),
                "std": std(vals),
                "ci95": ci95(vals),
            }
        )
    rows.sort(key=lambda r: r["mean"], reverse=True)
    rank = {r["group"]: i + 1 for i, r in enumerate(rows)}

    out = {"rows": rows, "rank": rank}
    out_json = pathlib.Path(args.output_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")

    lines: List[str] = []
    lines.append("# External Baseline Summary (Auto-generated)")
    lines.append("")
    lines.append(f"- Source: `{args.logs_dir}`")
    lines.append("")
    lines.append("| Rank | Group | N | Mean | Std | 95% CI |")
    lines.append("|---|---|---:|---:|---:|---:|")
    for row in rows:
        lines.append(
            f"| {rank[row['group']]} | {row['group']} | {row['n']} | "
            f"{row['mean']:.4f} | {row['std']:.4f} | {row['ci95']:.4f} |"
        )
    if not rows:
        lines.append("| - | _none_ | 0 | 0 | 0 | 0 |")

    out_md = pathlib.Path(args.output_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

