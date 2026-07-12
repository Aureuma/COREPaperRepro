#!/usr/bin/env python3
"""Compute effect-size and exact permutation-test statistics for external baseline suite."""

from __future__ import annotations

import argparse
import itertools
import json
import math
import pathlib
import random
from typing import Dict, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--logs-dir", default="output/corepaper_logs/experiments/external_latest")
    parser.add_argument("--output-json", default="output/corepaper_reports/ws5/statistical_effects.json")
    parser.add_argument("--output-md", default="output/corepaper_reports/ws5/statistical_effects.md")
    parser.add_argument("--reference-group", default="method")
    parser.add_argument("--comparators", default="baseline,ext1,ext2")
    parser.add_argument("--max-exact-combinations", type=int, default=1_000_000)
    parser.add_argument("--mc-samples", type=int, default=200_000)
    parser.add_argument("--mc-seed", type=int, default=7)
    return parser.parse_args()


def mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def std(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = mean(values)
    return math.sqrt(sum((v - m) ** 2 for v in values) / (len(values) - 1))


def group_from_run_id(run_id: str) -> str:
    if "-s" in run_id:
        return run_id.rsplit("-s", 1)[0]
    return run_id


def load_grouped_values(logs_dir: pathlib.Path) -> Dict[str, List[float]]:
    grouped: Dict[str, List[float]] = {}
    for path in sorted(logs_dir.glob("*.json")):
        if path.name == "suite_summary.json":
            continue
        row = json.loads(path.read_text(encoding="utf-8"))
        group = group_from_run_id(str(row.get("run_id", "")))
        value = row.get("metric_payload", {}).get("primary_metric")
        if value is None:
            continue
        grouped.setdefault(group, []).append(float(value))
    return grouped


def cohen_d(x: List[float], y: List[float]) -> float:
    if len(x) < 2 or len(y) < 2:
        return 0.0
    sx = std(x)
    sy = std(y)
    nx = len(x)
    ny = len(y)
    pooled_var = (((nx - 1) * sx * sx) + ((ny - 1) * sy * sy)) / max(1, (nx + ny - 2))
    pooled = math.sqrt(max(0.0, pooled_var))
    if pooled == 0.0:
        return 0.0
    return (mean(x) - mean(y)) / pooled


def permutation_pvalue(
    x: List[float],
    y: List[float],
    max_exact_combinations: int,
    mc_samples: int,
    mc_seed: int,
) -> Dict[str, float | int | str]:
    """Two-sided permutation p-value with exact/MC fallback by problem size."""
    observed = abs(mean(x) - mean(y))
    pooled = x + y
    n_x = len(x)
    if n_x == 0 or len(y) == 0:
        return {
            "p_value": 1.0,
            "mode": "degenerate",
            "total_combinations": 0,
            "samples_used": 0,
        }

    total_combinations = math.comb(len(pooled), n_x)
    idx = list(range(len(pooled)))

    if total_combinations <= max_exact_combinations:
        count_extreme = 0
        total = 0
        for subset in itertools.combinations(idx, n_x):
            subset_set = set(subset)
            group_a = [pooled[i] for i in subset_set]
            group_b = [pooled[i] for i in idx if i not in subset_set]
            diff = abs(mean(group_a) - mean(group_b))
            if diff >= observed - 1e-12:
                count_extreme += 1
            total += 1
        p_value = count_extreme / total if total else 1.0
        return {
            "p_value": p_value,
            "mode": "exact",
            "total_combinations": total_combinations,
            "samples_used": total,
        }

    rng = random.Random(mc_seed)
    count_extreme = 0
    samples_used = max(1, mc_samples)
    for _ in range(samples_used):
        subset = set(rng.sample(idx, n_x))
        group_a = [pooled[i] for i in subset]
        group_b = [pooled[i] for i in idx if i not in subset]
        diff = abs(mean(group_a) - mean(group_b))
        if diff >= observed - 1e-12:
            count_extreme += 1
    p_value = count_extreme / samples_used
    return {
        "p_value": p_value,
        "mode": "monte_carlo",
        "total_combinations": total_combinations,
        "samples_used": samples_used,
    }


def ci95_delta(x: List[float], y: List[float]) -> float:
    """Normal-approx CI half-width for difference in means."""
    if len(x) < 2 or len(y) < 2:
        return 0.0
    se = math.sqrt((std(x) ** 2 / len(x)) + (std(y) ** 2 / len(y)))
    return 1.96 * se


def worst(values: List[float]) -> float:
    return min(values) if values else 0.0


def cvar_bottom(values: List[float], fraction: float = 0.4) -> float:
    if not values:
        return 0.0
    k = max(1, int(round(len(values) * fraction)))
    sorted_vals = sorted(values)
    return mean(sorted_vals[:k])


def main() -> int:
    args = parse_args()
    logs_dir = pathlib.Path(args.logs_dir)
    grouped = load_grouped_values(logs_dir)

    ref = args.reference_group
    if ref not in grouped:
        raise SystemExit(f"Missing reference group '{ref}' in {logs_dir}")

    comparators = [c.strip() for c in args.comparators.split(",") if c.strip()]
    rows = []
    ref_values = grouped[ref]
    ref_mean = mean(ref_values)

    for comp in comparators:
        values = grouped.get(comp)
        if not values:
            continue
        comp_mean = mean(values)
        delta = ref_mean - comp_mean
        perm = permutation_pvalue(
            ref_values,
            values,
            max_exact_combinations=args.max_exact_combinations,
            mc_samples=args.mc_samples,
            mc_seed=args.mc_seed,
        )
        row = {
            "reference_group": ref,
            "comparator_group": comp,
            "n_reference": len(ref_values),
            "n_comparator": len(values),
            "reference_mean": ref_mean,
            "comparator_mean": comp_mean,
            "delta_mean": delta,
            "reference_worst": worst(ref_values),
            "comparator_worst": worst(values),
            "delta_worst": worst(ref_values) - worst(values),
            "reference_cvar40": cvar_bottom(ref_values, fraction=0.4),
            "comparator_cvar40": cvar_bottom(values, fraction=0.4),
            "delta_cvar40": cvar_bottom(ref_values, fraction=0.4) - cvar_bottom(values, fraction=0.4),
            "delta_ci95_halfwidth": ci95_delta(ref_values, values),
            "cohen_d": cohen_d(ref_values, values),
            "p_two_sided": perm["p_value"],
            "permutation_mode": perm["mode"],
            "permutation_total_combinations": perm["total_combinations"],
            "permutation_samples_used": perm["samples_used"],
        }
        rows.append(row)

    out = {
        "suite": str(logs_dir),
        "reference_group": ref,
        "rows": rows,
    }

    out_json = pathlib.Path(args.output_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")

    lines: List[str] = []
    lines.append("# Statistical Effect Summary (Auto-generated)")
    lines.append("")
    lines.append(f"- Source: `{logs_dir}`")
    lines.append(f"- Reference group: `{ref}`")
    lines.append("")
    lines.append("| Comparison | N (ref/comp) | Ref Mean | Comp Mean | Delta Mean | Ref Worst | Comp Worst | Delta Worst | Ref CVaR40 | Comp CVaR40 | Delta CVaR40 | CI95 (delta) | Cohen's d | p-value |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for row in rows:
        ci = row["delta_ci95_halfwidth"]
        lines.append(
            f"| {row['reference_group']} vs {row['comparator_group']} | "
            f"{row['n_reference']}/{row['n_comparator']} | "
            f"{row['reference_mean']:.4f} | {row['comparator_mean']:.4f} | "
            f"{row['delta_mean']:+.4f} | "
            f"{row['reference_worst']:.4f} | {row['comparator_worst']:.4f} | {row['delta_worst']:+.4f} | "
            f"{row['reference_cvar40']:.4f} | {row['comparator_cvar40']:.4f} | {row['delta_cvar40']:+.4f} | "
            f"±{ci:.4f} | {row['cohen_d']:.3f} | {row['p_two_sided']:.4f} ({row['permutation_mode']}) |"
        )
    if not rows:
        lines.append("| _none_ | 0/0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |")

    out_md = pathlib.Path(args.output_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
