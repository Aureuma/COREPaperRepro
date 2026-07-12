#!/usr/bin/env python3
"""Assess N=14 adaptmanip equivalence evidence from paired seed outcomes."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import pathlib
import random
from statistics import mean
from typing import Dict, Iterable, List, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-json",
        default="output/corepaper_reports/ws3/metaworld_seedexp_adaptmanip_method_results.json",
        help="Path to ws3 result bundle with per-episode records.",
    )
    parser.add_argument("--reference-variant", default="method")
    parser.add_argument("--comparator-variant", default="adaptmanip")
    parser.add_argument("--scenario", default="shifted")
    parser.add_argument(
        "--equivalence-margin",
        type=float,
        default=0.05,
        help="Two-sided practical-equivalence margin on success scale.",
    )
    parser.add_argument(
        "--bootstrap-samples",
        type=int,
        default=10000,
        help="Bootstrap resamples for CI/equivalence diagnostics.",
    )
    parser.add_argument("--random-seed", type=int, default=7)
    parser.add_argument(
        "--output-json",
        default="output/corepaper_reports/ws5/metaworld_adapt_equivalence_n14.json",
    )
    parser.add_argument(
        "--output-md",
        default="output/corepaper_reports/ws5/metaworld_adapt_equivalence_n14.md",
    )
    return parser.parse_args()


def _cvar_bottom(values: Iterable[float], *, fraction: float = 0.4) -> float:
    vals = sorted(float(v) for v in values)
    if not vals:
        return 0.0
    k = max(1, int(round(len(vals) * fraction)))
    return mean(vals[:k])


def _quantile(values: List[float], q: float) -> float:
    if not values:
        return 0.0
    if q <= 0.0:
        return min(values)
    if q >= 1.0:
        return max(values)
    xs = sorted(values)
    pos = (len(xs) - 1) * q
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return xs[lo]
    w = pos - lo
    return (1.0 - w) * xs[lo] + w * xs[hi]


def _seed_means(
    episodes: List[Dict],
    *,
    scenario: str,
    variant: str,
) -> Dict[int, float]:
    per_seed: Dict[int, List[float]] = {}
    for row in episodes:
        if str(row.get("scenario", "")) != scenario:
            continue
        if str(row.get("variant", "")) != variant:
            continue
        try:
            seed = int(row.get("seed"))
        except (TypeError, ValueError):
            continue
        per_seed.setdefault(seed, []).append(float(row.get("success_final", 0.0)))
    return {seed: mean(vals) for seed, vals in per_seed.items() if vals}


def _metric_row(
    *,
    name: str,
    observed_delta: float,
    bootstrap_values: List[float],
    margin: float,
) -> Dict:
    ci90_lo = _quantile(bootstrap_values, 0.05)
    ci90_hi = _quantile(bootstrap_values, 0.95)
    ci95_lo = _quantile(bootstrap_values, 0.025)
    ci95_hi = _quantile(bootstrap_values, 0.975)
    p_le_neg_margin = (
        sum(1 for v in bootstrap_values if v <= -margin) / len(bootstrap_values) if bootstrap_values else 1.0
    )
    p_ge_pos_margin = (
        sum(1 for v in bootstrap_values if v >= margin) / len(bootstrap_values) if bootstrap_values else 1.0
    )
    equivalence_supported = bool(ci90_lo >= -margin and ci90_hi <= margin)
    return {
        "metric": name,
        "observed_delta": float(observed_delta),
        "ci90_low": float(ci90_lo),
        "ci90_high": float(ci90_hi),
        "ci95_low": float(ci95_lo),
        "ci95_high": float(ci95_hi),
        "bootstrap_prob_le_neg_margin": float(p_le_neg_margin),
        "bootstrap_prob_ge_pos_margin": float(p_ge_pos_margin),
        "equivalence_supported": equivalence_supported,
    }


def _build_payload(args: argparse.Namespace) -> Dict:
    input_path = pathlib.Path(args.input_json)
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    episodes = payload.get("episodes", [])
    if not isinstance(episodes, list) or not episodes:
        raise ValueError("Missing non-empty episodes list in input JSON.")

    ref = str(args.reference_variant)
    comp = str(args.comparator_variant)
    scenario = str(args.scenario)
    margin = float(args.equivalence_margin)
    bootstrap_samples = int(args.bootstrap_samples)
    rng = random.Random(int(args.random_seed))

    ref_seed_means = _seed_means(episodes, scenario=scenario, variant=ref)
    comp_seed_means = _seed_means(episodes, scenario=scenario, variant=comp)
    shared = sorted(set(ref_seed_means) & set(comp_seed_means))
    if len(shared) < 8:
        raise ValueError(f"Expected at least 8 shared seeds, found {len(shared)}.")

    deltas = [float(ref_seed_means[s] - comp_seed_means[s]) for s in shared]
    observed_mean_delta = mean(deltas)
    observed_cvar_delta = _cvar_bottom(ref_seed_means[s] for s in shared) - _cvar_bottom(comp_seed_means[s] for s in shared)

    boot_mean: List[float] = []
    boot_cvar: List[float] = []
    for _ in range(max(100, bootstrap_samples)):
        sample = [shared[rng.randrange(0, len(shared))] for _ in range(len(shared))]
        sample_ref = [float(ref_seed_means[s]) for s in sample]
        sample_comp = [float(comp_seed_means[s]) for s in sample]
        sample_deltas = [r - c for r, c in zip(sample_ref, sample_comp)]
        boot_mean.append(mean(sample_deltas))
        boot_cvar.append(_cvar_bottom(sample_ref) - _cvar_bottom(sample_comp))

    metric_rows = [
        _metric_row(
            name="mean_seed_success",
            observed_delta=observed_mean_delta,
            bootstrap_values=boot_mean,
            margin=margin,
        ),
        _metric_row(
            name="cvar40_seed_success",
            observed_delta=observed_cvar_delta,
            bootstrap_values=boot_cvar,
            margin=margin,
        ),
    ]
    metric_lookup = {row["metric"]: row for row in metric_rows}

    return {
        "generated_at_utc": dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "input_json": str(input_path),
        "suite_name": str(payload.get("suite_name", "")),
        "scenario": scenario,
        "reference_variant": ref,
        "comparator_variant": comp,
        "n_shared_seeds": int(len(shared)),
        "shared_seeds": shared,
        "equivalence_margin_abs": float(margin),
        "bootstrap_samples": int(max(100, bootstrap_samples)),
        "metrics": metric_rows,
        "summary": {
            "mean_equivalence_supported": bool(
                metric_lookup["mean_seed_success"]["equivalence_supported"]
            ),
            "cvar_equivalence_supported": bool(
                metric_lookup["cvar40_seed_success"]["equivalence_supported"]
            ),
            "both_metrics_equivalence_supported": bool(
                metric_lookup["mean_seed_success"]["equivalence_supported"]
                and metric_lookup["cvar40_seed_success"]["equivalence_supported"]
            ),
            "interpretation": (
                "Equivalence is only supported when the 90% bootstrap CI lies fully inside "
                "[-margin, +margin] for the target metric."
            ),
        },
    }


def _markdown(payload: Dict) -> str:
    margin = float(payload.get("equivalence_margin_abs", 0.0))
    lines: List[str] = []
    lines.append("# Adaptmanip N=14 Equivalence Audit (Auto-generated)")
    lines.append("")
    lines.append(f"- Input: `{payload.get('input_json', '')}`")
    lines.append(f"- Scenario: `{payload.get('scenario', '')}`")
    lines.append(
        f"- Variants: `{payload.get('reference_variant', '')}` vs `{payload.get('comparator_variant', '')}`"
    )
    lines.append(f"- Shared seeds: {payload.get('n_shared_seeds', 0)}")
    lines.append(f"- Equivalence margin: ±{margin:.4f}")
    lines.append(f"- Bootstrap samples: {payload.get('bootstrap_samples', 0)}")
    lines.append("")
    lines.append(
        "| Metric | Observed delta | 90% CI | 95% CI | P(delta<=-margin) | P(delta>=+margin) | Equivalence supported |"
    )
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for row in payload.get("metrics", []):
        lines.append(
            f"| {row.get('metric')} | {float(row.get('observed_delta', 0.0)):+.4f} | "
            f"[{float(row.get('ci90_low', 0.0)):+.4f}, {float(row.get('ci90_high', 0.0)):+.4f}] | "
            f"[{float(row.get('ci95_low', 0.0)):+.4f}, {float(row.get('ci95_high', 0.0)):+.4f}] | "
            f"{float(row.get('bootstrap_prob_le_neg_margin', 0.0)):.4f} | "
            f"{float(row.get('bootstrap_prob_ge_pos_margin', 0.0)):.4f} | "
            f"{'yes' if bool(row.get('equivalence_supported', False)) else 'no'} |"
        )
    lines.append("")
    summary = payload.get("summary", {})
    lines.append(
        f"- Mean equivalence supported: {'yes' if bool(summary.get('mean_equivalence_supported', False)) else 'no'}"
    )
    lines.append(
        f"- CVaR equivalence supported: {'yes' if bool(summary.get('cvar_equivalence_supported', False)) else 'no'}"
    )
    lines.append("")
    lines.append(str(summary.get("interpretation", "")))
    return "\n".join(lines).strip() + "\n"


def main() -> int:
    args = parse_args()
    payload = _build_payload(args)

    out_json = pathlib.Path(args.output_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    out_md = pathlib.Path(args.output_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(_markdown(payload), encoding="utf-8")

    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
