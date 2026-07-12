#!/usr/bin/env python3
"""Compute statistical and reliability-floor summaries for MetaWorld slice results."""

from __future__ import annotations

import argparse
import itertools
import json
import math
import pathlib
import random
from collections import defaultdict
from typing import Callable, Dict, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-json", default="output/corepaper_reports/ws3/metaworld_slice_results.json")
    parser.add_argument("--output-json", default="output/corepaper_reports/ws3/metaworld_slice_stats.json")
    parser.add_argument("--output-md", default="output/corepaper_reports/ws3/metaworld_slice_stats.md")
    parser.add_argument("--scenario", default="shifted")
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


def cvar_bottom(values: List[float], fraction: float = 0.4) -> float:
    if not values:
        return 0.0
    k = max(1, int(round(len(values) * fraction)))
    return mean(sorted(values)[:k])


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
    statistic: Callable[[List[float]], float] | None = None,
) -> Dict[str, float | int | str]:
    stat_fn = statistic or mean
    observed = abs(stat_fn(x) - stat_fn(y))
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
            diff = abs(stat_fn(group_a) - stat_fn(group_b))
            if diff >= observed - 1e-12:
                count_extreme += 1
            total += 1
        return {
            "p_value": count_extreme / total if total else 1.0,
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
        diff = abs(stat_fn(group_a) - stat_fn(group_b))
        if diff >= observed - 1e-12:
            count_extreme += 1
    return {
        "p_value": count_extreme / samples_used,
        "mode": "monte_carlo",
        "total_combinations": total_combinations,
        "samples_used": samples_used,
    }


def ci95_delta(x: List[float], y: List[float]) -> float:
    if len(x) < 2 or len(y) < 2:
        return 0.0
    se = math.sqrt((std(x) ** 2 / len(x)) + (std(y) ** 2 / len(y)))
    return 1.96 * se


def main() -> int:
    args = parse_args()
    payload = json.loads(pathlib.Path(args.input_json).read_text(encoding="utf-8"))
    episodes = payload.get("episodes", [])

    by_variant_values: Dict[str, List[float]] = defaultdict(list)
    by_variant_steps: Dict[str, List[float]] = defaultdict(list)
    by_variant_seed_values: Dict[str, Dict[int, List[float]]] = defaultdict(lambda: defaultdict(list))

    for row in episodes:
        if row.get("scenario") != args.scenario:
            continue
        variant = str(row.get("variant"))
        value = float(row.get("success_final", 0.0))
        steps = float(row.get("steps_executed", 0.0))
        seed = int(row.get("seed", 0))
        by_variant_values[variant].append(value)
        by_variant_steps[variant].append(steps)
        by_variant_seed_values[variant][seed].append(value)

    variant_summary: Dict[str, Dict] = {}
    for variant in sorted(by_variant_values.keys()):
        values = by_variant_values[variant]
        steps = by_variant_steps[variant]
        seed_means = [mean(v) for _, v in sorted(by_variant_seed_values[variant].items())]
        total_steps = sum(steps)
        total_success = sum(values)
        variant_summary[variant] = {
            "n_episodes": len(values),
            "n_seeds": len(seed_means),
            "mean_success": mean(values),
            "worst_seed_mean": min(seed_means) if seed_means else 0.0,
            "cvar40_seed": cvar_bottom(seed_means, fraction=0.4),
            "mean_steps": mean(steps),
            "success_per_1k_steps": (1000.0 * total_success / total_steps) if total_steps > 0 else 0.0,
            "seed_means": seed_means,
        }

    reference = args.reference_group
    if reference not in by_variant_values:
        raise SystemExit(f"Missing reference group '{reference}' for scenario '{args.scenario}'.")

    comparisons: List[Dict] = []
    for comp in [c.strip() for c in args.comparators.split(",") if c.strip()]:
        if comp not in by_variant_values:
            continue
        ref_values = by_variant_values[reference]
        comp_values = by_variant_values[comp]
        ref_seed_means = [float(v) for v in variant_summary[reference]["seed_means"]]
        comp_seed_means = [float(v) for v in variant_summary[comp]["seed_means"]]
        perm_mean = permutation_pvalue(
            ref_values,
            comp_values,
            max_exact_combinations=args.max_exact_combinations,
            mc_samples=args.mc_samples,
            mc_seed=args.mc_seed,
        )
        perm_worst = permutation_pvalue(
            ref_seed_means,
            comp_seed_means,
            max_exact_combinations=args.max_exact_combinations,
            mc_samples=args.mc_samples,
            mc_seed=args.mc_seed,
            statistic=lambda vals: min(vals) if vals else 0.0,
        )
        perm_cvar = permutation_pvalue(
            ref_seed_means,
            comp_seed_means,
            max_exact_combinations=args.max_exact_combinations,
            mc_samples=args.mc_samples,
            mc_seed=args.mc_seed,
            statistic=lambda vals: cvar_bottom(vals, fraction=0.4),
        )
        comparisons.append(
            {
                "reference_group": reference,
                "comparator_group": comp,
                "n_reference": len(ref_values),
                "n_comparator": len(comp_values),
                "reference_mean": mean(ref_values),
                "comparator_mean": mean(comp_values),
                "delta_mean": mean(ref_values) - mean(comp_values),
                "reference_worst_seed_mean": variant_summary[reference]["worst_seed_mean"],
                "comparator_worst_seed_mean": variant_summary[comp]["worst_seed_mean"],
                "delta_worst_seed_mean": variant_summary[reference]["worst_seed_mean"]
                - variant_summary[comp]["worst_seed_mean"],
                "reference_cvar40_seed": variant_summary[reference]["cvar40_seed"],
                "comparator_cvar40_seed": variant_summary[comp]["cvar40_seed"],
                "delta_cvar40_seed": variant_summary[reference]["cvar40_seed"] - variant_summary[comp]["cvar40_seed"],
                "delta_ci95_halfwidth": ci95_delta(ref_values, comp_values),
                "cohen_d": cohen_d(ref_values, comp_values),
                "p_two_sided": perm_mean["p_value"],
                "p_two_sided_mean": perm_mean["p_value"],
                "p_two_sided_worst_seed": perm_worst["p_value"],
                "p_two_sided_cvar40_seed": perm_cvar["p_value"],
                "permutation_mode": perm_mean["mode"],
                "permutation_mode_mean": perm_mean["mode"],
                "permutation_mode_worst_seed": perm_worst["mode"],
                "permutation_mode_cvar40_seed": perm_cvar["mode"],
                "permutation_total_combinations": perm_mean["total_combinations"],
                "permutation_total_combinations_mean": perm_mean["total_combinations"],
                "permutation_total_combinations_worst_seed": perm_worst["total_combinations"],
                "permutation_total_combinations_cvar40_seed": perm_cvar["total_combinations"],
                "permutation_samples_used": perm_mean["samples_used"],
                "permutation_samples_used_mean": perm_mean["samples_used"],
                "permutation_samples_used_worst_seed": perm_worst["samples_used"],
                "permutation_samples_used_cvar40_seed": perm_cvar["samples_used"],
            }
        )

    total_episodes_all = len(episodes)
    total_episodes_scenario = sum(v["n_episodes"] for v in variant_summary.values())
    out_payload = {
        "input_json": args.input_json,
        "scenario": args.scenario,
        "reference_group": reference,
        "variant_summary": variant_summary,
        "comparisons": comparisons,
        "compute_profile": {
            "total_episodes_all_scenarios": total_episodes_all,
            "total_episodes_scenario": total_episodes_scenario,
            "training_loop": "none (evaluation-only benchmark slice)",
            "gpu_hours": 0.0,
        },
    }

    out_json = pathlib.Path(args.output_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(out_payload, indent=2) + "\n", encoding="utf-8")

    lines: List[str] = []
    lines.append("# MetaWorld Slice Statistical Summary (Auto-generated)")
    lines.append("")
    lines.append(f"- Input: `{args.input_json}`")
    lines.append(f"- Scenario: `{args.scenario}`")
    lines.append(f"- Reference group: `{reference}`")
    lines.append("")
    lines.append("## Variant Summary")
    lines.append("")
    lines.append("| Variant | N episodes | N seeds | Mean | Worst-seed mean | CVaR40 (seed) | Success/1k steps |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    preferred = [
        "baseline",
        "ext1",
        "ext2",
        "latency_aware",
        "adaptmanip",
        "robust_cp",
        "history_keyframe",
        "constrained_flow",
        "method",
    ]
    ordered_variants = [v for v in preferred if v in variant_summary]
    ordered_variants.extend(v for v in sorted(variant_summary.keys()) if v not in ordered_variants)
    for variant in ordered_variants:
        row = variant_summary.get(variant)
        if not row:
            continue
        lines.append(
            f"| {variant} | {row['n_episodes']} | {row['n_seeds']} | {row['mean_success']:.4f} | "
            f"{row['worst_seed_mean']:.4f} | {row['cvar40_seed']:.4f} | {row['success_per_1k_steps']:.3f} |"
        )
    lines.append("")
    lines.append("## Reference Comparisons")
    lines.append("")
    lines.append(
        "| Comparison | N (ref/comp) | Ref Mean | Comp Mean | Delta Mean | Delta CI95 | Delta Worst-seed | Delta CVaR40(seed) | Cohen's d | p(mean) | p(CVaR40) |"
    )
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for row in comparisons:
        lines.append(
            f"| {row['reference_group']} vs {row['comparator_group']} | "
            f"{row['n_reference']}/{row['n_comparator']} | "
            f"{row['reference_mean']:.4f} | {row['comparator_mean']:.4f} | {row['delta_mean']:+.4f} | "
            f"±{row['delta_ci95_halfwidth']:.4f} | {row['delta_worst_seed_mean']:+.4f} | "
            f"{row['delta_cvar40_seed']:+.4f} | {row['cohen_d']:.3f} | "
            f"{row['p_two_sided_mean']:.6f} ({row['permutation_mode_mean']}) | "
            f"{row['p_two_sided_cvar40_seed']:.6f} ({row['permutation_mode_cvar40_seed']}) |"
        )
    lines.append("")
    lines.append("## Compute Profile")
    lines.append("")
    lines.append(f"- Total episodes (all scenarios): `{total_episodes_all}`")
    lines.append(f"- Total episodes ({args.scenario}): `{total_episodes_scenario}`")
    lines.append("- Training loop: `none (evaluation-only benchmark slice)`")
    lines.append("- GPU-hours: `0.0`")

    out_md = pathlib.Path(args.output_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")

    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
