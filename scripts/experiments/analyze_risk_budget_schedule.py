#!/usr/bin/env python3
"""Analyze dynamic risk-budget and conformal-envelope behavior from run logs."""

from __future__ import annotations

import argparse
import json
import pathlib
from collections import defaultdict
from typing import Dict, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--logs-dir", default="output/corepaper_logs/experiments/recent_baselines_latest")
    parser.add_argument("--variant", default="method")
    parser.add_argument("--output-json", default="output/corepaper_reports/ws5/risk_budget_schedule.json")
    parser.add_argument("--output-md", default="output/corepaper_reports/ws5/risk_budget_schedule.md")
    return parser.parse_args()


def mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def load_rows(logs_dir: pathlib.Path, variant: str) -> List[Dict]:
    rows: List[Dict] = []
    for path in sorted(logs_dir.glob("*.json")):
        if path.name == "suite_summary.json":
            continue
        run = json.loads(path.read_text(encoding="utf-8"))
        payload = run.get("metric_payload", {}) or {}
        resolved_variant = str(payload.get("resolved_variant") or payload.get("variant") or "")
        if resolved_variant != variant:
            continue
        components = payload.get("score_components", {}) or {}
        if "risk_lambda" not in components:
            continue
        rows.append(
            {
                "run_id": str(run.get("run_id", path.stem)),
                "scenario": str(payload.get("scenario", "unknown")),
                "primary_metric": float(payload.get("primary_metric", 0.0)),
                "risk_lambda": float(components.get("risk_lambda", 1.0)),
                "severity_norm": float(components.get("severity_norm", 0.0)),
                "conformal_violation": float(components.get("conformal_violation", 0.0)),
                "total_penalty": float(components.get("total_penalty", 0.0)),
                "total_penalty_effective": float(components.get("total_penalty_effective", components.get("total_penalty", 0.0))),
            }
        )
    if not rows:
        raise ValueError(f"No rows for variant '{variant}' found in {logs_dir}")
    return rows


def summarize(rows: List[Dict]) -> Dict:
    by_scenario: Dict[str, List[Dict]] = defaultdict(list)
    for row in rows:
        by_scenario[row["scenario"]].append(row)

    scenario_rows: List[Dict] = []
    for scenario in sorted(by_scenario.keys()):
        group = by_scenario[scenario]
        scenario_rows.append(
            {
                "scenario": scenario,
                "n": len(group),
                "mean_score": mean([r["primary_metric"] for r in group]),
                "mean_risk_lambda": mean([r["risk_lambda"] for r in group]),
                "mean_severity_norm": mean([r["severity_norm"] for r in group]),
                "conformal_violation_rate": mean([r["conformal_violation"] for r in group]),
                "mean_penalty_raw": mean([r["total_penalty"] for r in group]),
                "mean_penalty_effective": mean([r["total_penalty_effective"] for r in group]),
            }
        )

    return {
        "n_rows": len(rows),
        "scenario_rows": scenario_rows,
        "global": {
            "mean_risk_lambda": mean([r["risk_lambda"] for r in rows]),
            "mean_conformal_violation_rate": mean([r["conformal_violation"] for r in rows]),
            "mean_penalty_raw": mean([r["total_penalty"] for r in rows]),
            "mean_penalty_effective": mean([r["total_penalty_effective"] for r in rows]),
        },
    }


def markdown(logs_dir: pathlib.Path, variant: str, payload: Dict) -> str:
    lines: List[str] = []
    lines.append("# Dynamic Risk-Budget and Conformal Envelope (Auto-generated)")
    lines.append("")
    lines.append(f"- Source logs: `{logs_dir}`")
    lines.append(f"- Variant: `{variant}`")
    lines.append(f"- Rows: {payload['n_rows']}")
    lines.append("")
    lines.append("| Scenario | N | Mean Score | Mean Risk Lambda | Mean Severity | Conformal Violation Rate | Mean Penalty Raw | Mean Penalty Effective |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for row in payload["scenario_rows"]:
        lines.append(
            f"| {row['scenario']} | {row['n']} | {row['mean_score']:.4f} | {row['mean_risk_lambda']:.4f} | "
            f"{row['mean_severity_norm']:.4f} | {row['conformal_violation_rate']:.3f} | "
            f"{row['mean_penalty_raw']:.4f} | {row['mean_penalty_effective']:.4f} |"
        )
    return "\n".join(lines).strip() + "\n"


def main() -> int:
    args = parse_args()
    logs_dir = pathlib.Path(args.logs_dir)
    rows = load_rows(logs_dir, variant=args.variant)
    payload = summarize(rows)

    out_json = pathlib.Path(args.output_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    out_md = pathlib.Path(args.output_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(markdown(logs_dir, args.variant, payload), encoding="utf-8")

    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

