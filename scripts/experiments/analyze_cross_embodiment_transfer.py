#!/usr/bin/env python3
"""Analyze cross-embodiment transfer quality from proxy benchmark episodes."""

from __future__ import annotations

import argparse
import json
import math
import pathlib
from collections import defaultdict
from typing import Dict, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-json", default="output/corepaper_reports/ws3/cross_embodiment_proxy_results.json")
    parser.add_argument("--output-json", default="output/corepaper_reports/ws3/cross_embodiment_proxy_stats.json")
    parser.add_argument("--output-md", default="output/corepaper_reports/ws3/cross_embodiment_proxy_stats.md")
    parser.add_argument("--scenario", default="shifted")
    parser.add_argument("--reference-group", default="method")
    parser.add_argument("--comparators", default="baseline,ext1,ext2,latency_aware,adaptmanip,robust_cp")
    return parser.parse_args()


def mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def std(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = mean(values)
    return math.sqrt(sum((v - m) ** 2 for v in values) / (len(values) - 1))


def cvar_bottom(values: List[float], frac: float = 0.4) -> float:
    if not values:
        return 0.0
    k = max(1, int(round(len(values) * frac)))
    return mean(sorted(values)[:k])


def ci95_delta(x: List[float], y: List[float]) -> float:
    if len(x) < 2 or len(y) < 2:
        return 0.0
    se = math.sqrt((std(x) ** 2 / len(x)) + (std(y) ** 2 / len(y)))
    return 1.96 * se


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


def approx_pvalue(x: List[float], y: List[float]) -> float:
    # Fast conservative z-approximation for deterministic proxy diagnostics.
    if len(x) < 2 or len(y) < 2:
        return 1.0
    m = mean(x) - mean(y)
    se = math.sqrt((std(x) ** 2 / len(x)) + (std(y) ** 2 / len(y)))
    if se <= 1e-12:
        return 1.0
    z = abs(m / se)
    return max(0.0, min(1.0, math.erfc(z / math.sqrt(2.0))))


def main() -> int:
    args = parse_args()
    payload = json.loads(pathlib.Path(args.input_json).read_text(encoding="utf-8"))
    episodes = payload.get("episodes", [])
    source = str(payload.get("source_embodiment", "franka"))

    by_variant_values: Dict[str, List[float]] = defaultdict(list)
    by_variant_steps: Dict[str, List[float]] = defaultdict(list)
    by_variant_seed_values: Dict[str, Dict[int, List[float]]] = defaultdict(lambda: defaultdict(list))
    cross_matrix: Dict[tuple[str, str], Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))

    for row in episodes:
        if str(row.get("scenario")) != args.scenario:
            continue
        if str(row.get("target_embodiment")) == source:
            continue
        variant = str(row.get("variant"))
        value = float(row.get("success_final", 0.0))
        steps = float(row.get("steps_executed", 0.0))
        seed = int(row.get("seed", 0))
        target = str(row.get("target_embodiment"))
        by_variant_values[variant].append(value)
        by_variant_steps[variant].append(steps)
        by_variant_seed_values[variant][seed].append(value)
        cross_matrix[(source, target)][variant].append(value)

    reference = args.reference_group
    if reference not in by_variant_values:
        raise SystemExit(f"Missing reference group '{reference}' in scenario '{args.scenario}'.")

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
            "n_cross_targets": len({k[1] for k, byv in cross_matrix.items() if variant in byv}),
            "mean_success": mean(values),
            "worst_seed_mean": min(seed_means) if seed_means else 0.0,
            "cvar40_seed": cvar_bottom(seed_means, frac=0.4),
            "mean_steps": mean(steps),
            "success_per_1k_steps": (1000.0 * total_success / total_steps) if total_steps > 0 else 0.0,
            "seed_means": seed_means,
        }

    comparisons: List[Dict] = []
    for comp in [c.strip() for c in args.comparators.split(",") if c.strip()]:
        if comp not in by_variant_values:
            continue
        ref_values = by_variant_values[reference]
        comp_values = by_variant_values[comp]
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
                "p_two_sided": approx_pvalue(ref_values, comp_values),
            }
        )

    transfer_matrix: List[Dict] = []
    for (src, tgt), by_variant in sorted(cross_matrix.items()):
        for variant, values in sorted(by_variant.items()):
            transfer_matrix.append(
                {
                    "source_embodiment": src,
                    "target_embodiment": tgt,
                    "variant": variant,
                    "n": len(values),
                    "mean_success": mean(values),
                    "cvar40": cvar_bottom(values, frac=0.4),
                }
            )

    out_payload = {
        "input_json": args.input_json,
        "scenario": args.scenario,
        "source_embodiment": source,
        "reference_group": reference,
        "variant_summary": variant_summary,
        "comparisons": comparisons,
        "transfer_matrix": transfer_matrix,
        "compute_profile": {
            "total_episodes": sum(v["n_episodes"] for v in variant_summary.values()),
            "training_loop": "none (evaluation-only cross-embodiment proxy)",
            "gpu_hours": 0.0,
        },
    }

    out_json = pathlib.Path(args.output_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(out_payload, indent=2) + "\n", encoding="utf-8")

    lines: List[str] = []
    lines.append("# Cross-Embodiment Transfer Statistical Summary (Auto-generated)")
    lines.append("")
    lines.append(f"- Input: `{args.input_json}`")
    lines.append(f"- Scenario: `{args.scenario}`")
    lines.append(f"- Source embodiment: `{source}`")
    lines.append(f"- Reference group: `{reference}`")
    lines.append("")
    lines.append("## Variant Summary")
    lines.append("")
    lines.append("| Variant | N episodes | N seeds | N targets | Mean | Worst-seed mean | CVaR40(seed) | Success/1k steps |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    preferred = ("baseline", "ext1", "ext2", "latency_aware", "adaptmanip", "robust_cp", "method")
    for variant in preferred:
        row = variant_summary.get(variant)
        if not row:
            continue
        lines.append(
            f"| {variant} | {row['n_episodes']} | {row['n_seeds']} | {row['n_cross_targets']} | {row['mean_success']:.4f} | "
            f"{row['worst_seed_mean']:.4f} | {row['cvar40_seed']:.4f} | {row['success_per_1k_steps']:.3f} |"
        )
    lines.append("")
    lines.append("## Reference Comparisons")
    lines.append("")
    lines.append(
        "| Comparison | N (ref/comp) | Delta Mean | Delta CI95 | Delta Worst-seed | Delta CVaR40(seed) | Cohen's d | p-value |"
    )
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for row in comparisons:
        lines.append(
            f"| {row['reference_group']} vs {row['comparator_group']} | {row['n_reference']}/{row['n_comparator']} | "
            f"{row['delta_mean']:+.4f} | ±{row['delta_ci95_halfwidth']:.4f} | {row['delta_worst_seed_mean']:+.4f} | "
            f"{row['delta_cvar40_seed']:+.4f} | {row['cohen_d']:.3f} | {row['p_two_sided']:.6f} |"
        )

    out_md = pathlib.Path(args.output_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")

    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
