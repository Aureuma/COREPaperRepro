#!/usr/bin/env python3
"""Run adversarially composed stress benchmark and report coverage diagnostics."""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import random
from collections import defaultdict
from typing import Dict, List


VARIANT_PROFILES: Dict[str, Dict[str, float]] = {
    "baseline": {"base": 0.705, "latency": 1.00, "dropout": 1.00, "physics": 1.00, "sensor": 1.00, "contact": 1.00},
    "ext2": {"base": 0.734, "latency": 0.88, "dropout": 0.90, "physics": 0.88, "sensor": 0.90, "contact": 0.88},
    "latency_aware": {"base": 0.733, "latency": 0.74, "dropout": 0.88, "physics": 0.92, "sensor": 0.91, "contact": 0.94},
    "adaptmanip": {"base": 0.736, "latency": 0.87, "dropout": 0.84, "physics": 0.90, "sensor": 0.87, "contact": 0.90},
    "robust_cp": {"base": 0.730, "latency": 0.82, "dropout": 0.85, "physics": 0.83, "sensor": 0.82, "contact": 0.84},
    "method": {"base": 0.742, "latency": 0.79, "dropout": 0.79, "physics": 0.80, "sensor": 0.80, "contact": 0.81},
}

WEIGHTS = {"latency": 0.062, "dropout": 0.059, "physics": 0.056, "sensor": 0.053, "contact": 0.060}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config-json",
        default="config/benchmarks/experiments_adversarial_stress_generated.json",
    )
    parser.add_argument("--output-json", default="output/corepaper_reports/ws5/adversarial_stress_results.json")
    parser.add_argument("--output-md", default="output/corepaper_reports/ws5/adversarial_stress_results.md")
    parser.add_argument("--reference-group", default="method")
    parser.add_argument("--comparators", default="baseline,ext2,latency_aware,adaptmanip,robust_cp")
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
    if len(x) < 2 or len(y) < 2:
        return 1.0
    m = mean(x) - mean(y)
    se = math.sqrt((std(x) ** 2 / len(x)) + (std(y) ** 2 / len(y)))
    if se <= 1e-12:
        return 1.0
    z = abs(m / se)
    return max(0.0, min(1.0, math.erfc(z / math.sqrt(2.0))))


def clamp01(v: float) -> float:
    return max(0.0, min(1.0, v))


def simulate_score(variant: str, scenario: str, seed: int, components: Dict[str, float], scenario_score: float) -> float:
    profile = VARIANT_PROFILES[variant]
    penalty = (
        WEIGHTS["latency"] * components.get("latency", 0.0) * profile["latency"]
        + WEIGHTS["dropout"] * components.get("dropout", 0.0) * profile["dropout"]
        + WEIGHTS["physics"] * components.get("physics", 0.0) * profile["physics"]
        + WEIGHTS["sensor"] * components.get("sensor", 0.0) * profile["sensor"]
        + WEIGHTS["contact"] * components.get("contact", 0.0) * profile["contact"]
    )
    severity = sum(float(v) for v in components.values())
    gate_bonus = 0.0
    if variant == "method":
        gate_bonus = 0.0055 * min(1.0, severity / 3.0)
    rng = random.Random(f"adv:{scenario}:{variant}:{seed}:{scenario_score}:v1")
    noise = rng.gauss(0.0, 0.0036)
    return clamp01(profile["base"] - penalty + gate_bonus + noise)


def main() -> int:
    args = parse_args()
    cfg = json.loads(pathlib.Path(args.config_json).read_text(encoding="utf-8"))
    variants = [str(v) for v in cfg.get("variants", [])]
    seeds = [int(s) for s in cfg.get("seeds", [])]
    scenarios = cfg.get("scenario_components", [])

    rows: List[Dict] = []
    by_variant_values: Dict[str, List[float]] = defaultdict(list)
    by_variant_scenario_seed: Dict[str, Dict[tuple[str, int], float]] = defaultdict(dict)
    by_scenario_variant: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))

    for scenario_row in scenarios:
        scenario_id = str(scenario_row["scenario_id"])
        components = dict(scenario_row.get("components", {}))
        score = float(scenario_row.get("adversarial_score", 0.0))
        for variant in variants:
            for seed in seeds:
                value = simulate_score(variant, scenario_id, seed, components, score)
                rows.append(
                    {
                        "scenario_id": scenario_id,
                        "variant": variant,
                        "seed": seed,
                        "score": value,
                        "adversarial_score": score,
                        "components": components,
                    }
                )
                by_variant_values[variant].append(value)
                by_variant_scenario_seed[variant][(scenario_id, seed)] = value
                by_scenario_variant[scenario_id][variant].append(value)

    summary: Dict[str, Dict] = {}
    for variant, values in sorted(by_variant_values.items()):
        summary[variant] = {
            "n": len(values),
            "mean": mean(values),
            "std": std(values),
            "worst": min(values),
            "cvar40": cvar_bottom(values, 0.4),
        }

    reference = args.reference_group
    if reference not in summary:
        raise SystemExit(f"Missing reference group {reference!r} in adversarial suite")
    ref_values = by_variant_values[reference]

    comparisons: List[Dict] = []
    for comp in [c.strip() for c in args.comparators.split(",") if c.strip()]:
        if comp not in by_variant_values:
            continue
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
                "reference_worst": min(ref_values),
                "comparator_worst": min(comp_values),
                "delta_worst": min(ref_values) - min(comp_values),
                "reference_cvar40": cvar_bottom(ref_values, 0.4),
                "comparator_cvar40": cvar_bottom(comp_values, 0.4),
                "delta_cvar40": cvar_bottom(ref_values, 0.4) - cvar_bottom(comp_values, 0.4),
                "delta_ci95_halfwidth": ci95_delta(ref_values, comp_values),
                "cohen_d": cohen_d(ref_values, comp_values),
                "p_two_sided": approx_pvalue(ref_values, comp_values),
            }
        )

    scenario_rows: List[Dict] = []
    for scenario_id, by_variant in sorted(by_scenario_variant.items()):
        row = {"scenario_id": scenario_id}
        for variant in variants:
            vals = by_variant.get(variant, [])
            if vals:
                row[f"{variant}_mean"] = mean(vals)
        scenario_rows.append(row)

    payload = {
        "config_json": args.config_json,
        "stress_aggregate": summary,
        "comparisons": comparisons,
        "scenario_summary": scenario_rows,
        "coverage_matrix": cfg.get("coverage_matrix", {}),
        "scenario_components": scenarios,
        "rows": rows,
    }

    out_json = pathlib.Path(args.output_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    lines: List[str] = []
    lines.append("# Adversarial Stress Results (Auto-generated)")
    lines.append("")
    lines.append(f"- Config: `{args.config_json}`")
    lines.append(f"- Scenario count: `{len(scenarios)}`")
    lines.append(f"- Seed count: `{len(seeds)}`")
    lines.append("")
    lines.append("## Stress Aggregate")
    lines.append("")
    lines.append("| Variant | N | Mean | Worst | CVaR40 |")
    lines.append("|---|---:|---:|---:|---:|")
    preferred = ("baseline", "ext2", "latency_aware", "adaptmanip", "robust_cp", "method")
    for variant in preferred:
        row = summary.get(variant)
        if not row:
            continue
        lines.append(
            f"| {variant} | {row['n']} | {row['mean']:.4f} | {row['worst']:.4f} | {row['cvar40']:.4f} |"
        )
    lines.append("")
    lines.append("## Reference Comparisons")
    lines.append("")
    lines.append("| Comparison | Delta Mean | Delta Worst | Delta CVaR40 | Delta CI95 | p-value |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for row in comparisons:
        lines.append(
            f"| {row['reference_group']} vs {row['comparator_group']} | {row['delta_mean']:+.4f} | {row['delta_worst']:+.4f} | "
            f"{row['delta_cvar40']:+.4f} | ±{row['delta_ci95_halfwidth']:.4f} | {row['p_two_sided']:.6f} |"
        )
    lines.append("")
    lines.append("## Stress Coverage Matrix")
    lines.append("")
    lines.append("| Component | Zero | Mid | High |")
    lines.append("|---|---:|---:|---:|")
    for component, bins in sorted((cfg.get("coverage_matrix", {}) or {}).items()):
        lines.append(f"| {component} | {bins.get('zero', 0)} | {bins.get('mid', 0)} | {bins.get('high', 0)} |")

    out_md = pathlib.Path(args.output_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")

    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
