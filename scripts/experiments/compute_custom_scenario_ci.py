#!/usr/bin/env python3
"""Compute confidence intervals and bootstrap delta intervals for scenario-model results."""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import random
from typing import Dict, List, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--logs-dir", default="output/corepaper_logs/experiments/external_latest")
    parser.add_argument("--seed-expansion-json", default="output/corepaper_reports/ws5/seed_expansion_method_vs_ext2.json")
    parser.add_argument("--bootstrap-samples", type=int, default=200000)
    parser.add_argument("--rng-seed", type=int, default=20260218)
    parser.add_argument("--output-json", default="output/corepaper_reports/ws5/custom_scenario_ci.json")
    parser.add_argument("--output-md", default="output/corepaper_reports/ws5/custom_scenario_ci.md")
    return parser.parse_args()


def mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def std(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    mu = mean(values)
    return math.sqrt(sum((v - mu) ** 2 for v in values) / (len(values) - 1))


def ci95(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    return 1.96 * std(values) / math.sqrt(len(values))


def percentile(sorted_values: List[float], q: float) -> float:
    if not sorted_values:
        return 0.0
    q = max(0.0, min(1.0, q))
    idx = q * (len(sorted_values) - 1)
    lo = int(math.floor(idx))
    hi = int(math.ceil(idx))
    if lo == hi:
        return sorted_values[lo]
    w = idx - lo
    return sorted_values[lo] * (1.0 - w) + sorted_values[hi] * w


def bootstrap_delta_ci(
    a: List[float],
    b: List[float],
    samples: int,
    rng_seed: int,
    alpha: float = 0.05,
) -> Tuple[float, float]:
    if not a or not b:
        return 0.0, 0.0
    rng = random.Random(rng_seed)
    deltas: List[float] = []
    n_a = len(a)
    n_b = len(b)
    for _ in range(samples):
        sample_a = [a[rng.randrange(n_a)] for _ in range(n_a)]
        sample_b = [b[rng.randrange(n_b)] for _ in range(n_b)]
        deltas.append(mean(sample_a) - mean(sample_b))
    deltas.sort()
    lo = percentile(deltas, alpha / 2.0)
    hi = percentile(deltas, 1.0 - (alpha / 2.0))
    return lo, hi


def group_from_run_id(run_id: str) -> str:
    if "-s" in run_id:
        return run_id.rsplit("-s", 1)[0]
    return run_id


def load_main_groups(logs_dir: pathlib.Path) -> Dict[str, List[float]]:
    grouped: Dict[str, List[float]] = {}
    for path in sorted(logs_dir.glob("*.json")):
        if path.name == "suite_summary.json":
            continue
        row = json.loads(path.read_text(encoding="utf-8"))
        run_id = str(row.get("run_id", ""))
        metric = row.get("metric_payload", {}).get("primary_metric")
        if not run_id or metric is None:
            continue
        grouped.setdefault(group_from_run_id(run_id), []).append(float(metric))
    return grouped


def main() -> int:
    args = parse_args()
    logs_dir = pathlib.Path(args.logs_dir)
    grouped = load_main_groups(logs_dir)
    required = ["baseline", "ext1", "ext2", "method"]
    missing = [g for g in required if g not in grouped]
    if missing:
        raise SystemExit(f"Missing groups in {logs_dir}: {missing}")

    seed_expansion = json.loads(pathlib.Path(args.seed_expansion_json).read_text(encoding="utf-8"))
    vals_n14_method = [float(v) for v in seed_expansion["rows"]["method"]["values"]]
    vals_n14_ext2 = [float(v) for v in seed_expansion["rows"]["ext2"]["values"]]

    vals_n5_method = [float(v) for v in grouped["method"]]
    vals_n5_ext2 = [float(v) for v in grouped["ext2"]]

    n5_lo, n5_hi = bootstrap_delta_ci(
        vals_n5_method,
        vals_n5_ext2,
        samples=args.bootstrap_samples,
        rng_seed=args.rng_seed,
    )
    n14_lo, n14_hi = bootstrap_delta_ci(
        vals_n14_method,
        vals_n14_ext2,
        samples=args.bootstrap_samples,
        rng_seed=args.rng_seed + 97,
    )

    summary_rows = []
    for group in required:
        values = grouped[group]
        summary_rows.append(
            {
                "group": group,
                "n": len(values),
                "mean": round(mean(values), 6),
                "std": round(std(values), 6),
                "ci95": round(ci95(values), 6),
            }
        )

    payload = {
        "source_logs_dir": str(logs_dir),
        "seed_expansion_source": str(args.seed_expansion_json),
        "bootstrap_samples": args.bootstrap_samples,
        "main_n5_summary": summary_rows,
        "delta_method_vs_ext2": {
            "n5": {
                "mean_delta": round(mean(vals_n5_method) - mean(vals_n5_ext2), 6),
                "bootstrap_ci95_low": round(n5_lo, 6),
                "bootstrap_ci95_high": round(n5_hi, 6),
            },
            "n14": {
                "mean_delta": round(mean(vals_n14_method) - mean(vals_n14_ext2), 6),
                "bootstrap_ci95_low": round(n14_lo, 6),
                "bootstrap_ci95_high": round(n14_hi, 6),
            },
        },
    }

    out_json = pathlib.Path(args.output_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    lines: List[str] = []
    lines.append("# Custom Scenario Confidence Summary (Auto-generated)")
    lines.append("")
    lines.append(f"- Source logs: `{logs_dir}`")
    lines.append(f"- Seed expansion source: `{args.seed_expansion_json}`")
    lines.append(f"- Bootstrap samples: `{args.bootstrap_samples}`")
    lines.append("")
    lines.append("## Main N=5 Group Means and CI95")
    lines.append("")
    lines.append("| Group | N | Mean | Std | CI95 |")
    lines.append("|---|---:|---:|---:|---:|")
    for row in summary_rows:
        lines.append(
            f"| {row['group']} | {row['n']} | {row['mean']:.4f} | "
            f"{row['std']:.4f} | ±{row['ci95']:.4f} |"
        )
    lines.append("")
    lines.append("## Method vs ext2 Mean-Delta Bootstrap CI95")
    lines.append("")
    lines.append("| Comparison | Mean Delta | Bootstrap CI95 |")
    lines.append("|---|---:|---:|")
    d5 = payload["delta_method_vs_ext2"]["n5"]
    d14 = payload["delta_method_vs_ext2"]["n14"]
    lines.append(
        f"| N=5 main suite | {d5['mean_delta']:+.4f} | "
        f"[{d5['bootstrap_ci95_low']:+.4f}, {d5['bootstrap_ci95_high']:+.4f}] |"
    )
    lines.append(
        f"| N=14 seed expansion | {d14['mean_delta']:+.4f} | "
        f"[{d14['bootstrap_ci95_low']:+.4f}, {d14['bootstrap_ci95_high']:+.4f}] |"
    )

    out_md = pathlib.Path(args.output_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")

    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
