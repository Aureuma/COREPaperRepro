#!/usr/bin/env python3
"""Analyze offline-to-online failure accounting and intervention burden."""

from __future__ import annotations

import argparse
import json
import pathlib
from collections import defaultdict
from typing import Dict, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--logs-dir", default="output/corepaper_logs/experiments/o2o_proxy_latest")
    parser.add_argument("--reference-group", default="method")
    parser.add_argument("--comparators", default="baseline,ext2,latency_aware,adaptmanip,robust_cp")
    parser.add_argument("--output-json", default="output/corepaper_reports/ws5/o2o_failure_accounting.json")
    parser.add_argument("--output-md", default="output/corepaper_reports/ws5/o2o_failure_accounting.md")
    return parser.parse_args()


def mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def load_rows(logs_dir: pathlib.Path) -> List[Dict]:
    rows: List[Dict] = []
    for path in sorted(logs_dir.glob("*.json")):
        if path.name == "suite_summary.json":
            continue
        raw = json.loads(path.read_text(encoding="utf-8"))
        metric = raw.get("metric_payload") or {}
        if not metric:
            continue
        if metric.get("status") != "ok":
            continue
        comp = metric.get("score_components") or {}
        row = {
            "variant": str(metric.get("resolved_variant", metric.get("variant", ""))),
            "scenario": str(metric.get("scenario", "")),
            "primary_metric": float(metric.get("primary_metric", 0.0)),
            "offline_score": float(comp.get("offline_score", 0.0)),
            "online_score": float(comp.get("online_score", 0.0)),
            "online_gain": float(comp.get("online_gain", 0.0)),
            "interventions": int(comp.get("interventions", 0)),
            "catastrophic_events": int(comp.get("catastrophic_events", 0)),
            "severity_norm": float(comp.get("severity_norm", 0.0)),
            "offline_steps": int(comp.get("offline_steps", 0)),
            "online_steps": int(comp.get("online_steps", 0)),
        }
        rows.append(row)
    return rows


def main() -> int:
    args = parse_args()
    logs_dir = pathlib.Path(args.logs_dir)
    rows = load_rows(logs_dir)
    if not rows:
        raise SystemExit(f"No valid rows found under {logs_dir}")

    by_variant: Dict[str, List[Dict]] = defaultdict(list)
    for row in rows:
        by_variant[row["variant"]].append(row)

    reference = args.reference_group
    if reference not in by_variant:
        raise SystemExit(f"Missing reference group '{reference}' in logs.")

    summary: Dict[str, Dict] = {}
    for variant, items in sorted(by_variant.items()):
        summary[variant] = {
            "n": len(items),
            "mean_online": mean([float(r["online_score"]) for r in items]),
            "mean_offline": mean([float(r["offline_score"]) for r in items]),
            "mean_gain": mean([float(r["online_gain"]) for r in items]),
            "mean_interventions": mean([float(r["interventions"]) for r in items]),
            "mean_catastrophic_events": mean([float(r["catastrophic_events"]) for r in items]),
            "catastrophic_total": int(sum(int(r["catastrophic_events"]) for r in items)),
            "interventions_total": int(sum(int(r["interventions"]) for r in items)),
        }

    comparisons: List[Dict] = []
    for comp in [c.strip() for c in args.comparators.split(",") if c.strip()]:
        if comp not in summary:
            continue
        comparisons.append(
            {
                "reference_group": reference,
                "comparator_group": comp,
                "delta_online": summary[reference]["mean_online"] - summary[comp]["mean_online"],
                "delta_gain": summary[reference]["mean_gain"] - summary[comp]["mean_gain"],
                "delta_interventions": summary[reference]["mean_interventions"] - summary[comp]["mean_interventions"],
                "delta_catastrophic_events": summary[reference]["mean_catastrophic_events"]
                - summary[comp]["mean_catastrophic_events"],
            }
        )

    payload = {
        "logs_dir": str(logs_dir),
        "reference_group": reference,
        "summary": summary,
        "comparisons": comparisons,
    }

    out_json = pathlib.Path(args.output_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    lines: List[str] = []
    lines.append("# Offline-to-Online Failure Accounting (Auto-generated)")
    lines.append("")
    lines.append(f"- Logs dir: `{logs_dir}`")
    lines.append(f"- Reference group: `{reference}`")
    lines.append("")
    lines.append("## Variant Summary")
    lines.append("")
    lines.append("| Variant | N | Mean Offline | Mean Online | Mean Gain | Mean Interventions | Mean Catastrophic Events |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    preferred = ("baseline", "ext2", "latency_aware", "adaptmanip", "robust_cp", "method")
    for variant in preferred:
        row = summary.get(variant)
        if not row:
            continue
        lines.append(
            f"| {variant} | {row['n']} | {row['mean_offline']:.4f} | {row['mean_online']:.4f} | {row['mean_gain']:+.4f} | "
            f"{row['mean_interventions']:.2f} | {row['mean_catastrophic_events']:.2f} |"
        )
    lines.append("")
    lines.append("## Reference Comparisons")
    lines.append("")
    lines.append("| Comparison | Delta Online | Delta Gain | Delta Interventions | Delta Catastrophic Events |")
    lines.append("|---|---:|---:|---:|---:|")
    for row in comparisons:
        lines.append(
            f"| {row['reference_group']} vs {row['comparator_group']} | {row['delta_online']:+.4f} | {row['delta_gain']:+.4f} | "
            f"{row['delta_interventions']:+.2f} | {row['delta_catastrophic_events']:+.2f} |"
        )

    out_md = pathlib.Path(args.output_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")

    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
