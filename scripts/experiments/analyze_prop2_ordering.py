#!/usr/bin/env python3
"""Quantify a proxy observability check for Proposition-2 ordering."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
from typing import Dict, List, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--logs-dir",
        default="output/corepaper_logs/experiments/recent_baselines_latest",
        help="Directory containing per-run JSON logs (excluding suite_summary.json).",
    )
    parser.add_argument(
        "--reference-variant",
        default="method",
        help="Variant interpreted as candidate for the proxy ordering check.",
    )
    parser.add_argument(
        "--comparators",
        default="adaptmanip,latency_aware",
        help="Comma-separated comparator variants interpreted as incumbent proxies.",
    )
    parser.add_argument(
        "--output-json",
        default="output/corepaper_reports/ws5/prop2_ordering_proxy.json",
    )
    parser.add_argument(
        "--output-md",
        default="output/corepaper_reports/ws5/prop2_ordering_proxy.md",
    )
    return parser.parse_args()


def _mean(values: List[float]) -> float:
    return (sum(values) / len(values)) if values else 0.0


def _load_index(logs_dir: pathlib.Path, allowed_variants: set[str]) -> Dict[Tuple[str, int], Dict[str, float]]:
    index: Dict[Tuple[str, int], Dict[str, float]] = {}
    for path in sorted(logs_dir.glob("*.json")):
        if path.name == "suite_summary.json":
            continue
        blob = json.loads(path.read_text(encoding="utf-8"))
        payload = blob.get("metric_payload", {}) or {}
        variant = str(payload.get("resolved_variant") or payload.get("variant") or "")
        if variant not in allowed_variants:
            continue
        scenario = str(payload.get("scenario") or "unknown")
        seed_raw = payload.get("seed")
        if seed_raw is None:
            continue
        try:
            seed = int(seed_raw)
        except (TypeError, ValueError):
            continue
        score = payload.get("score_components", {}) or {}
        if "total_penalty" not in score:
            continue
        uncertainty = abs(float(score["total_penalty"]))
        index.setdefault((scenario, seed), {})[variant] = uncertainty
    if not index:
        raise ValueError(f"No compatible rows found in {logs_dir}")
    return index


def _build_comparator_row(
    *,
    comparator: str,
    reference: str,
    index: Dict[Tuple[str, int], Dict[str, float]],
) -> Dict:
    diffs: List[float] = []
    paired = 0
    holds = 0
    violations = 0
    equals = 0
    for row in index.values():
        if reference not in row or comparator not in row:
            continue
        paired += 1
        u_inc = float(row[comparator])
        u_cand = float(row[reference])
        diff = u_inc - u_cand
        diffs.append(diff)
        if diff <= 1e-12:
            holds += 1
        if diff > 1e-12:
            violations += 1
        if abs(diff) <= 1e-12:
            equals += 1

    if paired == 0:
        return {
            "comparator": comparator,
            "paired_rows": 0,
            "condition_holds_count": 0,
            "condition_holds_rate": 0.0,
            "violation_count": 0,
            "violation_rate": 0.0,
            "equal_count": 0,
            "mean_u_inc_minus_u_cand": 0.0,
            "max_abs_u_inc_minus_u_cand": 0.0,
        }

    return {
        "comparator": comparator,
        "paired_rows": paired,
        "condition_holds_count": holds,
        "condition_holds_rate": holds / paired,
        "violation_count": violations,
        "violation_rate": violations / paired,
        "equal_count": equals,
        "mean_u_inc_minus_u_cand": _mean(diffs),
        "max_abs_u_inc_minus_u_cand": max(abs(v) for v in diffs),
    }


def _build_payload(
    *,
    logs_dir: pathlib.Path,
    reference: str,
    comparators: List[str],
) -> Dict:
    variants = set(comparators) | {reference}
    index = _load_index(logs_dir, variants)
    rows = [
        _build_comparator_row(comparator=comparator, reference=reference, index=index)
        for comparator in comparators
    ]

    total_pairs = sum(int(row["paired_rows"]) for row in rows)
    total_holds = sum(int(row["condition_holds_count"]) for row in rows)
    total_violations = sum(int(row["violation_count"]) for row in rows)
    payload = {
        "generated_at_utc": dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "source_logs_dir": str(logs_dir),
        "reference_variant": reference,
        "comparators": comparators,
        "rows": rows,
        "overall": {
            "paired_rows": total_pairs,
            "condition_holds_count": total_holds,
            "condition_holds_rate": (total_holds / total_pairs) if total_pairs else 0.0,
            "violation_count": total_violations,
            "violation_rate": (total_violations / total_pairs) if total_pairs else 0.0,
        },
        "proxy_definition": (
            "Prop-2 ordering proxy checks U_incumbent <= U_candidate on matched scenario+seed rows "
            "using per-run uncertainty proxy U := |total_penalty|."
        ),
    }
    return payload


def _markdown(payload: Dict) -> str:
    lines: List[str] = []
    lines.append("# Proposition-2 Ordering Proxy (Auto-generated)")
    lines.append("")
    lines.append(f"- Source logs: `{payload['source_logs_dir']}`")
    lines.append(f"- Reference variant (candidate proxy): `{payload['reference_variant']}`")
    lines.append(f"- Total paired rows: {payload['overall']['paired_rows']}")
    lines.append(f"- Overall hold rate: {payload['overall']['condition_holds_rate']:.3f}")
    lines.append(f"- Overall violation rate: {payload['overall']['violation_rate']:.3f}")
    lines.append("")
    lines.append("| Comparator (incumbent proxy) | Paired rows | Hold rate | Violation rate | Mean(U_inc-U_cand) | Max|U_inc-U_cand| |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for row in payload["rows"]:
        lines.append(
            f"| {row['comparator']} | {row['paired_rows']} | {row['condition_holds_rate']:.3f} | "
            f"{row['violation_rate']:.3f} | {row['mean_u_inc_minus_u_cand']:+.4f} | "
            f"{row['max_abs_u_inc_minus_u_cand']:.4f} |"
        )
    lines.append("")
    lines.append(
        "Note: this is an observability proxy on matched benchmark rows, not a direct per-iteration training-log replay."
    )
    return "\n".join(lines).strip() + "\n"


def main() -> int:
    args = parse_args()
    comparators = [item.strip() for item in str(args.comparators).split(",") if item.strip()]
    if not comparators:
        raise SystemExit("No comparators specified.")

    payload = _build_payload(
        logs_dir=pathlib.Path(args.logs_dir),
        reference=str(args.reference_variant).strip(),
        comparators=comparators,
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
