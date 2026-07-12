#!/usr/bin/env python3
"""Audit matched-budget parity from MetaWorld result bundles."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
from typing import Dict, List


DEFAULT_INPUT_JSONS = ",".join(
    [
        "output/corepaper_reports/ws3/metaworld_seedexp_latency_method_results.json",
        "output/corepaper_reports/ws3/metaworld_seedexp_latency_method_n30_results.json",
        "output/corepaper_reports/ws3/metaworld_seedexp_adaptmanip_method_results.json",
        "output/corepaper_reports/ws3/metaworld_seedexp_adaptmanip_method_n30_results.json",
    ]
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-jsons",
        default=DEFAULT_INPUT_JSONS,
        help="Comma-separated list of result JSON files from run_metaworld_slice.py.",
    )
    parser.add_argument(
        "--reference-variant",
        default="method",
        help="Variant used as reference when computing budget deltas.",
    )
    parser.add_argument(
        "--output-json",
        default="output/corepaper_reports/ws5/metaworld_budget_parity.json",
    )
    parser.add_argument(
        "--output-md",
        default="output/corepaper_reports/ws5/metaworld_budget_parity.md",
    )
    return parser.parse_args()


def _mean(values: List[float]) -> float:
    return (sum(values) / len(values)) if values else 0.0


def _aggregate_variant_rows(episodes: List[Dict]) -> Dict[str, Dict[str, float]]:
    grouped: Dict[str, Dict[str, float]] = {}
    for row in episodes:
        variant = str(row.get("variant", "unknown"))
        steps = float(row.get("steps_executed", 0.0))
        agg = grouped.setdefault(variant, {"episodes": 0.0, "total_steps": 0.0, "mean_steps": 0.0})
        agg["episodes"] += 1.0
        agg["total_steps"] += steps
    for agg in grouped.values():
        eps = agg["episodes"]
        agg["mean_steps"] = (agg["total_steps"] / eps) if eps > 0 else 0.0
    return grouped


def _suite_rows(result_path: pathlib.Path, reference: str) -> List[Dict]:
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    episodes = payload.get("episodes", [])
    if not isinstance(episodes, list) or not episodes:
        raise ValueError(f"Missing episodes in {result_path}")
    budget_policy = payload.get("budget_policy", {}) or {}
    grouped = _aggregate_variant_rows(episodes)
    if reference not in grouped:
        raise ValueError(f"Reference variant '{reference}' not present in {result_path}")

    rows: List[Dict] = []
    ref = grouped[reference]
    for comparator, comp in sorted(grouped.items()):
        if comparator == reference:
            continue
        rows.append(
            {
                "result_json": str(result_path),
                "suite_name": str(payload.get("suite_name", result_path.stem)),
                "comparator": comparator,
                "reference_variant": reference,
                "max_steps_per_episode": int(budget_policy.get("max_steps_per_episode", 0)),
                "extra_monitor_episodes": int(budget_policy.get("extra_monitor_episodes", 0)),
                "reference_episodes": int(ref["episodes"]),
                "comparator_episodes": int(comp["episodes"]),
                "delta_episodes": int(ref["episodes"] - comp["episodes"]),
                "reference_total_steps": float(ref["total_steps"]),
                "comparator_total_steps": float(comp["total_steps"]),
                "delta_total_steps": float(ref["total_steps"] - comp["total_steps"]),
                "reference_mean_steps": float(ref["mean_steps"]),
                "comparator_mean_steps": float(comp["mean_steps"]),
                "delta_mean_steps": float(ref["mean_steps"] - comp["mean_steps"]),
            }
        )
    if not rows:
        raise ValueError(f"No comparator rows found in {result_path}")
    return rows


def _build_payload(input_paths: List[pathlib.Path], reference: str) -> Dict:
    rows: List[Dict] = []
    for path in input_paths:
        rows.extend(_suite_rows(path, reference))

    max_abs_delta_episodes = max(abs(int(row["delta_episodes"])) for row in rows) if rows else 0
    max_abs_delta_total_steps = max(abs(float(row["delta_total_steps"])) for row in rows) if rows else 0.0
    max_abs_delta_mean_steps = max(abs(float(row["delta_mean_steps"])) for row in rows) if rows else 0.0
    max_extra_monitor = max(int(row["extra_monitor_episodes"]) for row in rows) if rows else 0

    payload = {
        "generated_at_utc": dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "reference_variant": reference,
        "rows": rows,
        "summary": {
            "n_rows": len(rows),
            "max_abs_delta_episodes": int(max_abs_delta_episodes),
            "max_abs_delta_total_steps": float(max_abs_delta_total_steps),
            "max_abs_delta_mean_steps": float(max_abs_delta_mean_steps),
            "max_extra_monitor_episodes": int(max_extra_monitor),
            "all_episode_deltas_zero": bool(max_abs_delta_episodes == 0),
            "all_total_step_deltas_zero": bool(abs(max_abs_delta_total_steps) <= 1e-12),
        },
    }
    return payload


def _markdown(payload: Dict) -> str:
    rows = payload["rows"]
    lines: List[str] = []
    lines.append("# MetaWorld Budget Parity Audit (Auto-generated)")
    lines.append("")
    lines.append(f"- Reference variant: `{payload['reference_variant']}`")
    lines.append(f"- Comparator rows: {payload['summary']['n_rows']}")
    lines.append(f"- Max |delta episodes|: {payload['summary']['max_abs_delta_episodes']}")
    lines.append(f"- Max |delta total steps|: {payload['summary']['max_abs_delta_total_steps']:.1f}")
    lines.append(f"- Max extra monitor episodes: {payload['summary']['max_extra_monitor_episodes']}")
    lines.append("")
    lines.append(
        "| Suite | Comparator | max steps/ep | extra monitor eps | delta episodes | delta total steps | delta mean steps |"
    )
    lines.append("|---|---|---:|---:|---:|---:|---:|")
    for row in rows:
        lines.append(
            f"| {row['suite_name']} | {row['comparator']} | {row['max_steps_per_episode']} | "
            f"{row['extra_monitor_episodes']} | {row['delta_episodes']} | {row['delta_total_steps']:.1f} | "
            f"{row['delta_mean_steps']:+.3f} |"
        )
    lines.append("")
    lines.append("All deltas are computed as reference minus comparator.")
    return "\n".join(lines).strip() + "\n"


def main() -> int:
    args = parse_args()
    input_paths = [pathlib.Path(item.strip()) for item in str(args.input_jsons).split(",") if item.strip()]
    if not input_paths:
        raise SystemExit("No input JSON files provided.")

    payload = _build_payload(input_paths=input_paths, reference=str(args.reference_variant).strip())

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
