#!/usr/bin/env python3
"""Diagnose ceiling-regime conditions behind near-parity mean deltas."""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Dict, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--recent-json",
        default="output/corepaper_reports/ws5/recent_paper_baselines.json",
    )
    parser.add_argument(
        "--metaworld-json",
        default="output/corepaper_reports/ws3/metaworld_seedexp_latency_method_n30_stats.json",
    )
    parser.add_argument(
        "--mean-gap-threshold",
        type=float,
        default=0.06,
        help="Maximum absolute mean delta considered near-parity.",
    )
    parser.add_argument(
        "--floor-gap-threshold",
        type=float,
        default=0.03,
        help="Minimum floor gap (worst/CVaR) treated as practically meaningful.",
    )
    parser.add_argument(
        "--ceiling-mean-threshold",
        type=float,
        default=0.62,
        help="Mean level above which the regime is treated as saturation-prone.",
    )
    parser.add_argument(
        "--output-json",
        default="output/corepaper_reports/ws5/ceiling_regime_diagnostics.json",
    )
    parser.add_argument(
        "--output-md",
        default="output/corepaper_reports/ws5/ceiling_regime_diagnostics.md",
    )
    return parser.parse_args()


def load_json(path: pathlib.Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def find_row(rows: List[Dict], comparator: str) -> Dict:
    for row in rows:
        if row.get("comparator_group") == comparator:
            return row
    raise KeyError(f"Missing comparator_group={comparator}")


def main() -> int:
    args = parse_args()
    recent = load_json(pathlib.Path(args.recent_json))
    meta = load_json(pathlib.Path(args.metaworld_json))

    ranking = recent.get("stress_ranking", [])
    if not ranking:
        raise SystemExit("Missing stress_ranking in recent baseline report.")
    top = ranking[0]
    runner_up = ranking[1] if len(ranking) > 1 else ranking[0]
    stress_mean_gap = float(top.get("mean", 0.0)) - float(runner_up.get("mean", 0.0))

    top_comp = str(runner_up.get("variant", ""))
    stress_comp_row = find_row(recent.get("comparisons", []), comparator=top_comp)
    stress_floor_gap = min(
        float(stress_comp_row.get("delta_worst", 0.0)),
        float(stress_comp_row.get("delta_cvar40", 0.0)),
    )

    meta_latency = find_row(meta.get("comparisons", []), comparator="latency_aware")
    meta_mean_gap = float(meta_latency.get("delta_mean", 0.0))
    meta_floor_gap = min(
        float(meta_latency.get("delta_worst_seed_mean", 0.0)),
        float(meta_latency.get("delta_cvar40_seed", 0.0)),
    )
    variant_summary = meta.get("variant_summary", {})
    method_mean = float(variant_summary.get("method", {}).get("mean_success", 0.0))

    near_parity = abs(meta_mean_gap) <= args.mean_gap_threshold
    floor_separation = meta_floor_gap >= args.floor_gap_threshold
    ceiling_level = method_mean >= args.ceiling_mean_threshold
    expected_ceiling_regime = near_parity and floor_separation and ceiling_level

    payload = {
        "thresholds": {
            "mean_gap_threshold": args.mean_gap_threshold,
            "floor_gap_threshold": args.floor_gap_threshold,
            "ceiling_mean_threshold": args.ceiling_mean_threshold,
        },
        "stress_track": {
            "top_variant": top.get("variant"),
            "runner_up_variant": runner_up.get("variant"),
            "top_mean": top.get("mean"),
            "runner_up_mean": runner_up.get("mean"),
            "top_mean_gap": stress_mean_gap,
            "top_floor_gap_min": stress_floor_gap,
        },
        "metaworld_n30_track": {
            "reference_variant": "method",
            "comparator_variant": "latency_aware",
            "reference_mean": method_mean,
            "mean_gap": meta_mean_gap,
            "floor_gap_min": meta_floor_gap,
            "mean_near_parity": near_parity,
            "floor_separation_positive": floor_separation,
            "ceiling_level_high": ceiling_level,
            "expected_ceiling_regime": expected_ceiling_regime,
            "p_two_sided": float(meta_latency.get("p_two_sided", 1.0)),
        },
        "interpretation": {
            "summary": (
                "Near-parity mean with positive floor separation in high-mean regime is consistent "
                "with ceiling effects."
                if expected_ceiling_regime
                else "Ceiling-regime criteria are not fully satisfied under configured thresholds."
            ),
            "recommendation": (
                "Prioritize worst-seed/CVaR and tail-risk metrics over mean-only interpretation."
            ),
        },
    }

    out_json = pathlib.Path(args.output_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    lines: List[str] = []
    lines.append("# Ceiling-Regime Diagnostics (Auto-generated)")
    lines.append("")
    lines.append("## Thresholds")
    lines.append("")
    lines.append(f"- mean gap threshold: {args.mean_gap_threshold:.4f}")
    lines.append(f"- floor gap threshold: {args.floor_gap_threshold:.4f}")
    lines.append(f"- ceiling mean threshold: {args.ceiling_mean_threshold:.4f}")
    lines.append("")
    lines.append("## MetaWorld N=30 (method vs latency_aware)")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|---|---:|")
    lines.append(f"| Mean gap | {meta_mean_gap:+.4f} |")
    lines.append(f"| Min floor gap (worst/CVaR) | {meta_floor_gap:+.4f} |")
    lines.append(f"| Reference mean | {method_mean:.4f} |")
    lines.append(f"| p-value | {float(meta_latency.get('p_two_sided', 1.0)):.4f} |")
    lines.append(f"| Mean near-parity | {'YES' if near_parity else 'NO'} |")
    lines.append(f"| Floor separation positive | {'YES' if floor_separation else 'NO'} |")
    lines.append(f"| Ceiling level high | {'YES' if ceiling_level else 'NO'} |")
    lines.append(f"| Expected ceiling regime | {'YES' if expected_ceiling_regime else 'NO'} |")
    lines.append("")
    lines.append("## Stress Aggregate Cross-check")
    lines.append("")
    lines.append("| Top variant | Runner-up | Mean gap | Min floor gap |")
    lines.append("|---|---|---:|---:|")
    lines.append(
        f"| {top.get('variant')} | {runner_up.get('variant')} | {stress_mean_gap:+.4f} | {stress_floor_gap:+.4f} |"
    )
    lines.append("")
    lines.append(f"- Interpretation: {payload['interpretation']['summary']}")
    lines.append(f"- Recommendation: {payload['interpretation']['recommendation']}")

    out_md = pathlib.Path(args.output_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")

    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

