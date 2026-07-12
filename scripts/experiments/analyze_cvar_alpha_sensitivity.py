#!/usr/bin/env python3
"""Compute CVaR-alpha sensitivity from MetaWorld seed-level slice outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-json", required=True, help="Path to run_metaworld_slice JSON output.")
    parser.add_argument("--scenario", default="shifted", help="Scenario subset to analyze.")
    parser.add_argument("--reference-group", default="method", help="Reference variant name.")
    parser.add_argument("--comparator-group", default="latency_aware", help="Comparator variant name.")
    parser.add_argument(
        "--alphas",
        default="0.1,0.2,0.3,0.4,0.5",
        help="Comma-separated CVaR alpha values in (0,1].",
    )
    parser.add_argument("--output-json", required=True, help="Output JSON path.")
    parser.add_argument("--output-md", required=True, help="Output markdown path.")
    return parser.parse_args()


def _mean(values: list[float]) -> float:
    return float(sum(values) / len(values)) if values else 0.0


def _cvar(values: list[float], alpha: float) -> tuple[float, int]:
    if not values:
        return 0.0, 0
    k = max(1, int(round(alpha * len(values))))
    return _mean(sorted(values)[:k]), k


def _seed_means(payload: dict, scenario: str, variant: str) -> list[float]:
    episodes = payload.get("episodes", [])
    seed_to_scores: dict[int, list[float]] = {}
    for row in episodes:
        if not isinstance(row, dict):
            continue
        if row.get("scenario") != scenario or row.get("variant") != variant:
            continue
        seed = row.get("seed")
        score = row.get("success_final")
        if not isinstance(seed, int):
            continue
        if not isinstance(score, (int, float)):
            continue
        seed_to_scores.setdefault(seed, []).append(float(score))
    means: list[float] = []
    for seed in sorted(seed_to_scores):
        means.append(_mean(seed_to_scores[seed]))
    return means


def _to_markdown(rows: list[dict], ref: str, comp: str) -> str:
    lines = [
        "# CVaR Alpha Sensitivity",
        "",
        f"Reference: `{ref}`",
        f"Comparator: `{comp}`",
        "",
        "| alpha | k | ref_CVaR | comp_CVaR | delta |",
        "|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| "
            f"{row['alpha']:.1f} | {row['k_reference']} | "
            f"{row['reference_cvar']:.4f} | {row['comparator_cvar']:.4f} | {row['delta_cvar']:+.4f} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    in_path = Path(args.input_json)
    payload = json.loads(in_path.read_text(encoding="utf-8"))

    alphas: list[float] = []
    for raw in args.alphas.split(","):
        raw = raw.strip()
        if not raw:
            continue
        alpha = float(raw)
        if alpha <= 0.0 or alpha > 1.0:
            raise ValueError(f"Invalid alpha {alpha}; expected 0 < alpha <= 1")
        alphas.append(alpha)
    if not alphas:
        raise ValueError("No valid alphas provided.")

    ref_values = _seed_means(payload, args.scenario, args.reference_group)
    comp_values = _seed_means(payload, args.scenario, args.comparator_group)
    if not ref_values or not comp_values:
        raise ValueError("No seed-level values found for reference/comparator in selected scenario.")

    rows: list[dict] = []
    for alpha in alphas:
        ref_cvar, ref_k = _cvar(ref_values, alpha)
        comp_cvar, comp_k = _cvar(comp_values, alpha)
        rows.append(
            {
                "alpha": alpha,
                "k_reference": ref_k,
                "k_comparator": comp_k,
                "reference_cvar": ref_cvar,
                "comparator_cvar": comp_cvar,
                "delta_cvar": ref_cvar - comp_cvar,
            }
        )

    out = {
        "input_json": str(in_path),
        "scenario": args.scenario,
        "reference_group": args.reference_group,
        "comparator_group": args.comparator_group,
        "n_reference": len(ref_values),
        "n_comparator": len(comp_values),
        "rows": rows,
    }

    out_json = Path(args.output_json)
    out_md = Path(args.output_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    out_md.write_text(
        _to_markdown(rows, args.reference_group, args.comparator_group),
        encoding="utf-8",
    )
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
