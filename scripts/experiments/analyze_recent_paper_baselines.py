#!/usr/bin/env python3
"""Analyze recent-paper-inspired baseline comparisons on scenario-model runs."""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import random
from collections import defaultdict
from typing import Dict, List


RECENT_VARIANTS = ("latency_aware", "adaptmanip", "robust_cp", "history_keyframe", "constrained_flow")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--logs-dir", default="output/corepaper_logs/experiments/recent_baselines_latest")
    parser.add_argument("--output-json", default="output/corepaper_reports/ws5/recent_paper_baselines.json")
    parser.add_argument("--output-md", default="output/corepaper_reports/ws5/recent_paper_baselines.md")
    parser.add_argument("--reference-group", default="method")
    parser.add_argument(
        "--comparators",
        default="baseline,ext1,ext2,latency_aware,adaptmanip,robust_cp,history_keyframe,constrained_flow",
    )
    parser.add_argument("--stress-scenarios", default="R4-hard,S1-hard,S2-high,S3-severe,SIM-isaac")
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


def ci95(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    return 1.96 * std(values) / math.sqrt(len(values))


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
) -> Dict[str, float | int | str]:
    observed = abs(mean(x) - mean(y))
    pooled = x + y
    n_x = len(x)
    if n_x == 0 or len(y) == 0:
        return {"p_value": 1.0, "mode": "degenerate", "total_combinations": 0, "samples_used": 0}

    total_combinations = math.comb(len(pooled), n_x)
    idx = list(range(len(pooled)))
    if total_combinations <= max_exact_combinations:
        import itertools

        count_extreme = 0
        total = 0
        for subset in itertools.combinations(idx, n_x):
            subset_set = set(subset)
            group_a = [pooled[i] for i in subset_set]
            group_b = [pooled[i] for i in idx if i not in subset_set]
            if abs(mean(group_a) - mean(group_b)) >= observed - 1e-12:
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
        if abs(mean(group_a) - mean(group_b)) >= observed - 1e-12:
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


def load_rows(logs_dir: pathlib.Path) -> List[Dict]:
    rows: List[Dict] = []
    for path in sorted(logs_dir.glob("*.json")):
        if path.name == "suite_summary.json":
            continue
        run = json.loads(path.read_text(encoding="utf-8"))
        metric = run.get("metric_payload", {})
        scenario = str(metric.get("scenario", ""))
        variant = str(metric.get("resolved_variant") or metric.get("variant", ""))
        value = metric.get("primary_metric")
        if not scenario or not variant or value is None:
            continue
        rows.append(
            {
                "scenario": scenario,
                "variant": variant,
                "score": float(value),
            }
        )
    return rows


def main() -> int:
    args = parse_args()
    logs_dir = pathlib.Path(args.logs_dir)
    rows = load_rows(logs_dir)
    if not rows:
        raise SystemExit(f"No runs found in {logs_dir}")

    stress_scenarios = tuple(s.strip() for s in args.stress_scenarios.split(",") if s.strip())
    by_scenario_variant: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
    by_variant_all: Dict[str, List[float]] = defaultdict(list)
    for row in rows:
        by_scenario_variant[row["scenario"]][row["variant"]].append(row["score"])
        by_variant_all[row["variant"]].append(row["score"])

    variant_names = sorted(by_variant_all.keys())
    scenario_names = sorted(by_scenario_variant.keys())

    scenario_summary: Dict[str, Dict[str, Dict[str, float]]] = {}
    for scenario in scenario_names:
        scenario_summary[scenario] = {}
        for variant in variant_names:
            values = by_scenario_variant[scenario].get(variant, [])
            if not values:
                continue
            scenario_summary[scenario][variant] = {
                "n": len(values),
                "mean": mean(values),
                "std": std(values),
                "ci95": ci95(values),
                "worst": min(values),
                "cvar40": cvar_bottom(values, 0.4),
            }

    stress_aggregate: Dict[str, Dict[str, float]] = {}
    for variant in variant_names:
        values: List[float] = []
        for scenario in stress_scenarios:
            values.extend(by_scenario_variant.get(scenario, {}).get(variant, []))
        if not values:
            continue
        stress_aggregate[variant] = {
            "n": len(values),
            "mean": mean(values),
            "std": std(values),
            "ci95": ci95(values),
            "worst": min(values),
            "cvar40": cvar_bottom(values, 0.4),
        }

    ranking = sorted(
        [{"variant": k, **v} for k, v in stress_aggregate.items()],
        key=lambda x: x["mean"],
        reverse=True,
    )

    reference = args.reference_group
    if reference not in stress_aggregate:
        raise SystemExit(f"Reference variant '{reference}' missing in stress aggregate")

    ref_values: List[float] = []
    for scenario in stress_scenarios:
        ref_values.extend(by_scenario_variant.get(scenario, {}).get(reference, []))

    comparisons: List[Dict] = []
    comparators = [c.strip() for c in args.comparators.split(",") if c.strip()]
    for comp in comparators:
        if comp == reference:
            continue
        comp_values: List[float] = []
        for scenario in stress_scenarios:
            comp_values.extend(by_scenario_variant.get(scenario, {}).get(comp, []))
        if not comp_values:
            continue
        perm = permutation_pvalue(
            ref_values,
            comp_values,
            max_exact_combinations=args.max_exact_combinations,
            mc_samples=args.mc_samples,
            mc_seed=args.mc_seed,
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
                "reference_worst": min(ref_values),
                "comparator_worst": min(comp_values),
                "delta_worst": min(ref_values) - min(comp_values),
                "reference_cvar40": cvar_bottom(ref_values, 0.4),
                "comparator_cvar40": cvar_bottom(comp_values, 0.4),
                "delta_cvar40": cvar_bottom(ref_values, 0.4) - cvar_bottom(comp_values, 0.4),
                "delta_ci95_halfwidth": ci95_delta(ref_values, comp_values),
                "cohen_d": cohen_d(ref_values, comp_values),
                "p_two_sided": perm["p_value"],
                "permutation_mode": perm["mode"],
                "permutation_total_combinations": perm["total_combinations"],
                "permutation_samples_used": perm["samples_used"],
            }
        )

    recent_rows = [row for row in ranking if row["variant"] in RECENT_VARIANTS]
    strongest_recent = recent_rows[0] if recent_rows else None
    strongest_any = ranking[0] if ranking else None
    guidance: List[str] = []
    if strongest_any and strongest_any["variant"] == reference:
        guidance.append("Keep CORE as primary method claim: top stress aggregate across comparators.")
    else:
        guidance.append("CORE is not top on stress aggregate; narrow claims or retune method before submission.")
    if strongest_recent:
        guidance.append(
            f"Closest recent-paper baseline is `{strongest_recent['variant']}` (stress mean {strongest_recent['mean']:.4f}); "
            "prioritize analysis against this baseline in text and figures."
        )
    guidance.append("Report stress aggregate and reliability-floor metrics jointly; avoid mean-only framing.")

    payload = {
        "suite": str(logs_dir),
        "stress_scenarios": list(stress_scenarios),
        "reference_group": reference,
        "scenario_summary": scenario_summary,
        "stress_aggregate": stress_aggregate,
        "stress_ranking": ranking,
        "comparisons": comparisons,
        "guidance": guidance,
    }

    out_json = pathlib.Path(args.output_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    preferred_order = [
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
    lines: List[str] = []
    lines.append("# Recent-Paper Baseline Comparison (Auto-generated)")
    lines.append("")
    lines.append(f"- Source: `{logs_dir}`")
    lines.append(f"- Stress scenarios: `{', '.join(stress_scenarios)}`")
    lines.append(f"- Reference group: `{reference}`")
    lines.append("")
    lines.append("## Stress Aggregate Ranking")
    lines.append("")
    lines.append("| Rank | Variant | N | Mean | CI95 | Worst | CVaR40 |")
    lines.append("|---:|---|---:|---:|---:|---:|---:|")
    for idx, row in enumerate(ranking, start=1):
        lines.append(
            f"| {idx} | {row['variant']} | {row['n']} | {row['mean']:.4f} | "
            f"±{row['ci95']:.4f} | {row['worst']:.4f} | {row['cvar40']:.4f} |"
        )

    lines.append("")
    lines.append("## Scenario Means")
    lines.append("")
    lines.append("| Scenario | " + " | ".join(preferred_order) + " |")
    lines.append("|---|" + "|".join(["---:"] * len(preferred_order)) + "|")
    for scenario in sorted(scenario_summary.keys()):
        vals = []
        for variant in preferred_order:
            v = scenario_summary[scenario].get(variant, {}).get("mean")
            vals.append(f"{v:.4f}" if v is not None else "-")
        lines.append(f"| {scenario} | " + " | ".join(vals) + " |")

    lines.append("")
    lines.append("## Method vs Comparator (Stress Aggregate)")
    lines.append("")
    lines.append("| Comparison | Delta Mean | Delta CI95 | Delta Worst | Delta CVaR40 | Cohen's d | p-value |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for row in comparisons:
        lines.append(
            f"| {row['reference_group']} vs {row['comparator_group']} | "
            f"{row['delta_mean']:+.4f} | ±{row['delta_ci95_halfwidth']:.4f} | "
            f"{row['delta_worst']:+.4f} | {row['delta_cvar40']:+.4f} | "
            f"{row['cohen_d']:.3f} | {row['p_two_sided']:.6f} ({row['permutation_mode']}) |"
        )

    lines.append("")
    lines.append("## Guidance")
    lines.append("")
    for row in guidance:
        lines.append(f"- {row}")

    out_md = pathlib.Path(args.output_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
