#!/usr/bin/env python3
"""Targeted seed-expansion analysis for narrow-margin comparisons."""

from __future__ import annotations

import argparse
import itertools
import json
import math
import pathlib
import random
from typing import Dict, List

from software_benchmark import simulate_score


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant-a", default="method")
    parser.add_argument("--variant-b", default="ext2")
    parser.add_argument("--scenario", default="nominal")
    parser.add_argument("--seed-start", type=int, default=1)
    parser.add_argument("--seed-end", type=int, default=14)
    parser.add_argument(
        "--max-exact-combinations",
        type=int,
        default=500000,
        help="Max combinations before switching to Monte Carlo permutation test.",
    )
    parser.add_argument("--monte-carlo-samples", type=int, default=200000)
    parser.add_argument("--rng-seed", type=int, default=20260218)
    parser.add_argument("--output-json", default="output/corepaper_reports/ws5/seed_expansion_method_vs_ext2.json")
    parser.add_argument("--output-md", default="output/corepaper_reports/ws5/seed_expansion_method_vs_ext2.md")
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


def cvar_bottom(values: List[float], frac: float = 0.4) -> float:
    if not values:
        return 0.0
    k = max(1, int(round(len(values) * frac)))
    return mean(sorted(values)[:k])


def evaluate_variant(variant: str, scenario: str, seeds: List[int]) -> List[float]:
    out = []
    for seed in seeds:
        run_id = f"{variant}-seedexp-s{seed}"
        payload = simulate_score(variant=variant, scenario=scenario, seed=seed, run_id=run_id)
        out.append(float(payload["score"]))
    return out


def exact_or_monte_carlo_pvalue(
    a: List[float],
    b: List[float],
    max_exact_combinations: int,
    monte_carlo_samples: int,
    rng_seed: int,
) -> Dict:
    observed = abs(mean(a) - mean(b))
    pooled = a + b
    n_a = len(a)
    total_combos = math.comb(len(pooled), n_a)

    if total_combos <= max_exact_combinations:
        count_extreme = 0
        total = 0
        idx = list(range(len(pooled)))
        for subset in itertools.combinations(idx, n_a):
            subset_set = set(subset)
            group_a = [pooled[i] for i in subset_set]
            group_b = [pooled[i] for i in idx if i not in subset_set]
            diff = abs(mean(group_a) - mean(group_b))
            if diff >= observed - 1e-12:
                count_extreme += 1
            total += 1
        return {
            "p_value": (count_extreme / total) if total else 1.0,
            "mode": "exact",
            "total_combinations": total_combos,
            "samples_used": total,
        }

    rng = random.Random(rng_seed)
    count_extreme = 0
    idx = list(range(len(pooled)))
    for _ in range(monte_carlo_samples):
        rng.shuffle(idx)
        group_a_idx = idx[:n_a]
        group_b_idx = idx[n_a:]
        group_a = [pooled[i] for i in group_a_idx]
        group_b = [pooled[i] for i in group_b_idx]
        diff = abs(mean(group_a) - mean(group_b))
        if diff >= observed - 1e-12:
            count_extreme += 1

    p_hat = count_extreme / monte_carlo_samples if monte_carlo_samples > 0 else 1.0
    return {
        "p_value": p_hat,
        "mode": "monte_carlo",
        "total_combinations": total_combos,
        "samples_used": monte_carlo_samples,
    }


def main() -> int:
    args = parse_args()
    if args.seed_end < args.seed_start:
        raise SystemExit("--seed-end must be >= --seed-start.")
    seeds = list(range(args.seed_start, args.seed_end + 1))

    vals_a = evaluate_variant(args.variant_a, args.scenario, seeds)
    vals_b = evaluate_variant(args.variant_b, args.scenario, seeds)
    test = exact_or_monte_carlo_pvalue(
        vals_a,
        vals_b,
        max_exact_combinations=args.max_exact_combinations,
        monte_carlo_samples=args.monte_carlo_samples,
        rng_seed=args.rng_seed,
    )

    payload = {
        "scenario": args.scenario,
        "seed_range": [args.seed_start, args.seed_end],
        "n_per_variant": len(seeds),
        "variant_a": args.variant_a,
        "variant_b": args.variant_b,
        "rows": {
            args.variant_a: {
                "mean": round(mean(vals_a), 6),
                "std": round(std(vals_a), 6),
                "ci95": round(ci95(vals_a), 6),
                "worst": round(min(vals_a), 6),
                "cvar40": round(cvar_bottom(vals_a), 6),
                "values": [round(v, 6) for v in vals_a],
            },
            args.variant_b: {
                "mean": round(mean(vals_b), 6),
                "std": round(std(vals_b), 6),
                "ci95": round(ci95(vals_b), 6),
                "worst": round(min(vals_b), 6),
                "cvar40": round(cvar_bottom(vals_b), 6),
                "values": [round(v, 6) for v in vals_b],
            },
        },
        "delta": {
            "mean": round(mean(vals_a) - mean(vals_b), 6),
            "worst": round(min(vals_a) - min(vals_b), 6),
            "cvar40": round(cvar_bottom(vals_a) - cvar_bottom(vals_b), 6),
        },
        "permutation_test": {
            "p_two_sided": round(float(test["p_value"]), 6),
            "mode": test["mode"],
            "total_combinations": int(test["total_combinations"]),
            "samples_used": int(test["samples_used"]),
        },
    }

    out_json = pathlib.Path(args.output_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    row_a = payload["rows"][args.variant_a]
    row_b = payload["rows"][args.variant_b]
    lines: List[str] = []
    lines.append("# Seed Expansion Report (Auto-generated)")
    lines.append("")
    lines.append(
        f"- Comparison: `{args.variant_a}` vs `{args.variant_b}` on `{args.scenario}` "
        f"(seeds {args.seed_start}-{args.seed_end}, N={payload['n_per_variant']} per variant)"
    )
    lines.append(
        f"- Permutation test: mode={payload['permutation_test']['mode']}, "
        f"p={payload['permutation_test']['p_two_sided']:.6f}, "
        f"samples={payload['permutation_test']['samples_used']}"
    )
    lines.append("")
    lines.append("| Variant | N | Mean | CI95 | Worst | CVaR40 |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    lines.append(
        f"| {args.variant_a} | {payload['n_per_variant']} | {row_a['mean']:.4f} | ±{row_a['ci95']:.4f} | "
        f"{row_a['worst']:.4f} | {row_a['cvar40']:.4f} |"
    )
    lines.append(
        f"| {args.variant_b} | {payload['n_per_variant']} | {row_b['mean']:.4f} | ±{row_b['ci95']:.4f} | "
        f"{row_b['worst']:.4f} | {row_b['cvar40']:.4f} |"
    )
    lines.append("")
    lines.append("| Delta Metric | Value |")
    lines.append("|---|---:|")
    lines.append(f"| Mean ({args.variant_a} - {args.variant_b}) | {payload['delta']['mean']:+.4f} |")
    lines.append(f"| Worst ({args.variant_a} - {args.variant_b}) | {payload['delta']['worst']:+.4f} |")
    lines.append(f"| CVaR40 ({args.variant_a} - {args.variant_b}) | {payload['delta']['cvar40']:+.4f} |")

    out_md = pathlib.Path(args.output_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")

    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
