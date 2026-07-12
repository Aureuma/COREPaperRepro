#!/usr/bin/env python3
"""Estimate current statistical power and seed budget recommendations."""

from __future__ import annotations

import argparse
import json
import math
import pathlib
from typing import Dict, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--effects-json", required=True)
    parser.add_argument("--target-power", type=float, default=0.80)
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument(
        "--sigma-floor",
        type=float,
        default=0.005,
        help="Conservative lower bound on pooled sigma for planning under optimistic variance.",
    )
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-md", required=True)
    return parser.parse_args()


def phi(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def pooled_sigma(delta: float, cohen_d: float) -> float:
    if abs(cohen_d) < 1e-12:
        return 0.0
    return abs(delta / cohen_d)


def power_two_sided(delta: float, sigma: float, n_per_group: int, z_alpha: float) -> float:
    if sigma <= 0.0 or n_per_group <= 0:
        return 0.0
    se = sigma * math.sqrt(2.0 / n_per_group)
    z_effect = abs(delta) / se
    # Approximation for two-sided z-test power.
    return max(0.0, min(1.0, 1.0 - phi(z_alpha - z_effect) + phi(-z_alpha - z_effect)))


def required_n(delta: float, sigma: float, z_alpha: float, z_power: float) -> int:
    if sigma <= 0.0 or abs(delta) <= 1e-12:
        return 9999
    n = 2.0 * ((z_alpha + z_power) ** 2) * (sigma**2) / (delta**2)
    return max(2, math.ceil(n))


def main() -> int:
    args = parse_args()
    effects = json.loads(pathlib.Path(args.effects_json).read_text(encoding="utf-8"))
    rows_in: List[Dict] = effects.get("rows", [])
    if not rows_in:
        raise SystemExit(f"No rows found in {args.effects_json}")

    # Conservative fixed z-values for lightweight planning.
    z_alpha = 1.96  # alpha ~= 0.05, two-sided
    z_power = 0.84  # power ~= 0.80

    rows_out: List[Dict] = []
    for row in rows_in:
        delta = float(row.get("delta_mean", 0.0))
        d = float(row.get("cohen_d", 0.0))
        n_ref = int(row.get("n_reference", 0))
        sigma = pooled_sigma(delta=delta, cohen_d=d)
        power_now = power_two_sided(delta=delta, sigma=sigma, n_per_group=n_ref, z_alpha=z_alpha)
        n_target = required_n(delta=delta, sigma=sigma, z_alpha=z_alpha, z_power=z_power)
        sigma_conservative = max(sigma, args.sigma_floor)
        power_now_conservative = power_two_sided(
            delta=delta,
            sigma=sigma_conservative,
            n_per_group=n_ref,
            z_alpha=z_alpha,
        )
        n_target_conservative = required_n(
            delta=delta,
            sigma=sigma_conservative,
            z_alpha=z_alpha,
            z_power=z_power,
        )
        rows_out.append(
            {
                "comparison": f"{row.get('reference_group')} vs {row.get('comparator_group')}",
                "delta_mean": delta,
                "cohen_d": d,
                "pooled_sigma_est": sigma,
                "n_current": n_ref,
                "power_est_current": power_now,
                "n_recommended_for_target_power": n_target,
                "sigma_for_conservative_planning": sigma_conservative,
                "power_est_current_conservative": power_now_conservative,
                "n_recommended_for_target_power_conservative": n_target_conservative,
            }
        )

    out = {
        "target_power": args.target_power,
        "alpha": args.alpha,
        "sigma_floor": args.sigma_floor,
        "method": "normal_approximation_from_observed_effects",
        "rows": rows_out,
    }

    out_json = pathlib.Path(args.output_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")

    lines: List[str] = []
    lines.append("# Statistical Power Report (Auto-generated)")
    lines.append("")
    lines.append(f"- Source effects: `{args.effects_json}`")
    lines.append(f"- Target power: {args.target_power:.2f}")
    lines.append(f"- Alpha: {args.alpha:.2f} (two-sided)")
    lines.append(f"- Conservative sigma floor: {args.sigma_floor:.4f}")
    lines.append("")
    lines.append(
        "| Comparison | Delta Mean | Cohen's d | Pooled Sigma (est) | N current | Power@N (est) | N rec. (est) | Power@N (conservative) | N rec. (conservative) |"
    )
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for row in rows_out:
        lines.append(
            f"| {row['comparison']} | {row['delta_mean']:+.4f} | {row['cohen_d']:.3f} | "
            f"{row['pooled_sigma_est']:.4f} | {row['n_current']} | {row['power_est_current']:.3f} | "
            f"{row['n_recommended_for_target_power']} | {row['power_est_current_conservative']:.3f} | "
            f"{row['n_recommended_for_target_power_conservative']} |"
        )

    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "- Use this as planning guidance for seed budget. Small deltas with lower effect size need larger `N` even when point estimates are positive."
    )
    lines.append(
        "- Current estimates are model-based approximations and should be treated as conservative planning signals, not definitive guarantees."
    )

    out_md = pathlib.Path(args.output_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")

    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
