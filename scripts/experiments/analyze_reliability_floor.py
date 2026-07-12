#!/usr/bin/env python3
"""Compute reliability-floor diagnostics for strongest baseline comparison."""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Dict, List, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--logs-dir", default="output/corepaper_logs/experiments/external_latest")
    parser.add_argument("--reference-group", default="method")
    parser.add_argument("--comparator-group", default="ext2")
    parser.add_argument(
        "--failure-threshold",
        type=float,
        default=0.7420,
        help="Seed success below this threshold is counted as failure-tail event.",
    )
    parser.add_argument("--output-json", default="output/corepaper_reports/ws5/reliability_floor.json")
    parser.add_argument("--output-md", default="output/corepaper_reports/ws5/reliability_floor.md")
    return parser.parse_args()


def group_from_run_id(run_id: str) -> str:
    if "-s" in run_id:
        return run_id.rsplit("-s", 1)[0]
    return run_id


def mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def cvar_bottom(values: List[float], fraction: float = 0.4) -> float:
    if not values:
        return 0.0
    k = max(1, int(round(len(values) * fraction)))
    sorted_vals = sorted(values)
    return mean(sorted_vals[:k])


def load_grouped_values(logs_dir: pathlib.Path) -> Dict[str, List[float]]:
    grouped: Dict[str, List[float]] = {}
    for path in sorted(logs_dir.glob("*.json")):
        if path.name == "suite_summary.json":
            continue
        row = json.loads(path.read_text(encoding="utf-8"))
        run_id = str(row.get("run_id", ""))
        metric = row.get("metric_payload", {}).get("primary_metric")
        if metric is None:
            continue
        grouped.setdefault(group_from_run_id(run_id), []).append(float(metric))
    return grouped


def histogram_counts(values: List[float], bins: List[Tuple[float, float]]) -> List[int]:
    counts = []
    for lo, hi in bins:
        c = 0
        for v in values:
            if lo <= v < hi or (hi == bins[-1][1] and lo <= v <= hi):
                c += 1
        counts.append(c)
    return counts


def build_payload(reference: List[float], comparator: List[float], failure_threshold: float) -> Dict:
    ref_sorted = sorted(reference)
    comp_sorted = sorted(comparator)

    all_values = ref_sorted + comp_sorted
    lo = min(all_values) - 0.0001
    hi = max(all_values) + 0.0001
    span = max(0.0001, hi - lo)
    step = span / 4.0
    bins = [
        (lo + i * step, lo + (i + 1) * step) for i in range(4)
    ]

    ref_tail_count = sum(1 for v in ref_sorted if v < failure_threshold)
    comp_tail_count = sum(1 for v in comp_sorted if v < failure_threshold)

    return {
        "failure_threshold": failure_threshold,
        "reference": {
            "name": "method",
            "values": ref_sorted,
            "mean": round(mean(ref_sorted), 4),
            "worst": round(min(ref_sorted), 4),
            "cvar40": round(cvar_bottom(ref_sorted, fraction=0.4), 4),
            "failure_tail_count": ref_tail_count,
            "failure_tail_rate": round(ref_tail_count / len(ref_sorted), 4),
            "hist_counts": histogram_counts(ref_sorted, bins),
        },
        "comparator": {
            "name": "ext2",
            "values": comp_sorted,
            "mean": round(mean(comp_sorted), 4),
            "worst": round(min(comp_sorted), 4),
            "cvar40": round(cvar_bottom(comp_sorted, fraction=0.4), 4),
            "failure_tail_count": comp_tail_count,
            "failure_tail_rate": round(comp_tail_count / len(comp_sorted), 4),
            "hist_counts": histogram_counts(comp_sorted, bins),
        },
        "bins": [
            {"low": round(lo, 4), "high": round(hi, 4)} for lo, hi in bins
        ],
    }


def markdown(payload: Dict) -> str:
    lines: List[str] = []
    lines.append("# Reliability-Floor Report (Auto-generated)")
    lines.append("")
    lines.append(f"- Failure threshold: `{payload['failure_threshold']:.4f}`")
    lines.append("- Comparison: `method` vs `ext2`")
    lines.append("")
    lines.append("| Group | Mean | Worst Seed | CVaR40 | Tail Count | Tail Rate |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for key in ("reference", "comparator"):
        row = payload[key]
        lines.append(
            f"| {row['name']} | {row['mean']:.4f} | {row['worst']:.4f} | {row['cvar40']:.4f} | "
            f"{row['failure_tail_count']} | {row['failure_tail_rate']:.2f} |"
        )
    lines.append("")
    lines.append("## Histogram Bins")
    lines.append("")
    lines.append("| Bin Range | method Count | ext2 Count |")
    lines.append("|---|---:|---:|")
    for idx, b in enumerate(payload["bins"]):
        ref_c = payload["reference"]["hist_counts"][idx]
        comp_c = payload["comparator"]["hist_counts"][idx]
        lines.append(f"| [{b['low']:.4f}, {b['high']:.4f}] | {ref_c} | {comp_c} |")
    return "\n".join(lines).strip() + "\n"


def main() -> int:
    args = parse_args()
    logs_dir = pathlib.Path(args.logs_dir)
    grouped = load_grouped_values(logs_dir)
    if args.reference_group not in grouped:
        raise SystemExit(f"Missing reference group '{args.reference_group}' in {logs_dir}")
    if args.comparator_group not in grouped:
        raise SystemExit(f"Missing comparator group '{args.comparator_group}' in {logs_dir}")

    payload = build_payload(
        reference=grouped[args.reference_group],
        comparator=grouped[args.comparator_group],
        failure_threshold=args.failure_threshold,
    )
    payload["reference"]["name"] = args.reference_group
    payload["comparator"]["name"] = args.comparator_group

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
