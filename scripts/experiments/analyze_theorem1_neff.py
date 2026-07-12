#!/usr/bin/env python3
"""Estimate effective sample size diagnostics for Theorem-1 independence caveat."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
from typing import Dict, List


DEFAULT_INPUT_JSONS = ",".join(
    [
        "output/corepaper_reports/ws3/metaworld_seedexp_latency_method_n30_results.json",
        "output/corepaper_reports/ws3/metaworld_seedexp_adaptmanip_method_n30_results.json",
    ]
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-jsons",
        default=DEFAULT_INPUT_JSONS,
        help="Comma-separated list of deep matched-seed result bundles.",
    )
    parser.add_argument(
        "--reference-variant",
        default="method",
        help="Reference variant used in per-row delta computation.",
    )
    parser.add_argument(
        "--scenario",
        default="shifted",
        help="Scenario filter for episodes.",
    )
    parser.add_argument(
        "--output-json",
        default="output/corepaper_reports/ws5/theorem1_neff_diagnostic.json",
    )
    parser.add_argument(
        "--output-md",
        default="output/corepaper_reports/ws5/theorem1_neff_diagnostic.md",
    )
    return parser.parse_args()


def _mean(values: List[float]) -> float:
    return (sum(values) / len(values)) if values else 0.0


def _clip(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _estimate_cluster_icc(clusters: Dict[int, List[float]]) -> Dict[str, float]:
    non_empty = {k: v for k, v in clusters.items() if v}
    k = len(non_empty)
    n = sum(len(v) for v in non_empty.values())
    if k < 2 or n <= k:
        return {
            "n_observations": float(n),
            "n_clusters": float(k),
            "mean_cluster_size": (float(n) / float(k)) if k > 0 else 0.0,
            "icc_seed_cluster": 0.0,
            "design_effect": 1.0,
            "n_eff_estimate": float(n),
        }

    cluster_means = {seed: _mean(vals) for seed, vals in non_empty.items()}
    grand = _mean([val for vals in non_empty.values() for val in vals])
    m_bar = float(n) / float(k)

    ss_between = sum(len(non_empty[seed]) * ((cluster_means[seed] - grand) ** 2) for seed in non_empty)
    ss_within = sum(sum((x - cluster_means[seed]) ** 2 for x in vals) for seed, vals in non_empty.items())

    df_between = max(1, k - 1)
    df_within = max(1, n - k)
    ms_between = ss_between / float(df_between)
    ms_within = ss_within / float(df_within)

    denom = ms_between + (m_bar - 1.0) * ms_within
    if denom <= 1e-12:
        icc = 0.0
    else:
        icc = (ms_between - ms_within) / denom
    icc = _clip(float(icc), 0.0, 0.99)

    design_effect = 1.0 + max(0.0, m_bar - 1.0) * icc
    n_eff = float(n) / design_effect if design_effect > 0.0 else float(n)
    n_eff = _clip(n_eff, 1.0, float(n))

    return {
        "n_observations": float(n),
        "n_clusters": float(k),
        "mean_cluster_size": m_bar,
        "icc_seed_cluster": icc,
        "design_effect": design_effect,
        "n_eff_estimate": n_eff,
    }


def _pairwise_delta_rows(
    *,
    payload: Dict,
    reference: str,
    scenario: str,
) -> Dict:
    episodes = payload.get("episodes", [])
    if not isinstance(episodes, list) or not episodes:
        raise ValueError("Missing non-empty episodes list.")

    filtered = [row for row in episodes if str(row.get("scenario", "")) == scenario]
    if not filtered:
        raise ValueError(f"No episodes for scenario={scenario!r}.")

    variants = sorted({str(row.get("variant", "")) for row in filtered if row.get("variant") is not None})
    comparators = [v for v in variants if v and v != reference]
    if len(comparators) != 1:
        raise ValueError(f"Expected exactly one comparator variant, found {comparators}")
    comparator = comparators[0]

    idx: Dict[tuple[str, int], Dict[str, float]] = {}
    for row in filtered:
        try:
            seed = int(row.get("seed"))
        except (TypeError, ValueError):
            continue
        task = str(row.get("task", "")).strip()
        variant = str(row.get("variant", "")).strip()
        if not task or variant not in {reference, comparator}:
            continue
        score = float(row.get("success_final", 0.0))
        idx.setdefault((task, seed), {})[variant] = score

    clusters: Dict[int, List[float]] = {}
    paired_rows = 0
    for (task, seed), pair in idx.items():
        if reference not in pair or comparator not in pair:
            continue
        paired_rows += 1
        delta = float(pair[reference]) - float(pair[comparator])
        clusters.setdefault(seed, []).append(delta)

    if paired_rows < 20:
        raise ValueError(f"Too few paired rows ({paired_rows}); expected >=20.")

    est = _estimate_cluster_icc(clusters)
    return {
        "suite_name": str(payload.get("suite_name", "unknown-suite")),
        "comparator": comparator,
        "reference_variant": reference,
        "scenario": scenario,
        "paired_rows": int(paired_rows),
        "n_seeds": int(est["n_clusters"]),
        "mean_tasks_per_seed": float(est["mean_cluster_size"]),
        "icc_seed_cluster": float(est["icc_seed_cluster"]),
        "design_effect": float(est["design_effect"]),
        "n_eff_estimate": float(est["n_eff_estimate"]),
    }


def _build_payload(input_paths: List[pathlib.Path], reference: str, scenario: str) -> Dict:
    rows: List[Dict] = []
    for path in input_paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        row = _pairwise_delta_rows(payload=payload, reference=reference, scenario=scenario)
        row["result_json"] = str(path)
        rows.append(row)

    min_neff = min(float(row["n_eff_estimate"]) for row in rows) if rows else 1.0
    max_icc = max(float(row["icc_seed_cluster"]) for row in rows) if rows else 0.0
    min_ratio = min(
        float(row["n_eff_estimate"]) / max(1.0, float(row["paired_rows"]))
        for row in rows
    ) if rows else 1.0

    return {
        "generated_at_utc": dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "reference_variant": reference,
        "scenario": scenario,
        "rows": rows,
        "summary": {
            "n_rows": len(rows),
            "min_n_eff_estimate": float(min_neff),
            "min_n_eff_estimate_floor": int(max(1, min_neff)),
            "min_n_eff_ratio": float(min_ratio),
            "max_icc_seed_cluster": float(max_icc),
        },
        "methodology": (
            "Per matched (task, seed) pair, compute delta := success_final(reference)-success_final(comparator). "
            "Estimate one-way seed-cluster ICC and design effect; report n_eff := n / design_effect as a conservative "
            "dependence diagnostic for Theorem-1 interpretation."
        ),
    }


def _markdown(payload: Dict) -> str:
    lines: List[str] = []
    lines.append("# Theorem-1 Effective Sample Size Diagnostic (Auto-generated)")
    lines.append("")
    lines.append(f"- Reference variant: `{payload['reference_variant']}`")
    lines.append(f"- Scenario: `{payload['scenario']}`")
    lines.append(f"- Min n_eff estimate: {payload['summary']['min_n_eff_estimate']:.1f}")
    lines.append(f"- Conservative floor(min n_eff): {payload['summary']['min_n_eff_estimate_floor']}")
    lines.append(f"- Max seed-cluster ICC: {payload['summary']['max_icc_seed_cluster']:.3f}")
    lines.append("")
    lines.append("| Suite | Comparator | Paired rows | Seeds | Mean tasks/seed | ICC(seed) | Design effect | n_eff |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|")
    for row in payload["rows"]:
        lines.append(
            f"| {row['suite_name']} | {row['comparator']} | {row['paired_rows']} | {row['n_seeds']} | "
            f"{row['mean_tasks_per_seed']:.2f} | {row['icc_seed_cluster']:.3f} | "
            f"{row['design_effect']:.3f} | {row['n_eff_estimate']:.1f} |"
        )
    lines.append("")
    lines.append(payload["methodology"])
    return "\n".join(lines).strip() + "\n"


def main() -> int:
    args = parse_args()
    input_paths = [pathlib.Path(item.strip()) for item in str(args.input_jsons).split(",") if item.strip()]
    if not input_paths:
        raise SystemExit("No input JSONs provided.")

    payload = _build_payload(
        input_paths=input_paths,
        reference=str(args.reference_variant).strip(),
        scenario=str(args.scenario).strip(),
    )

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
