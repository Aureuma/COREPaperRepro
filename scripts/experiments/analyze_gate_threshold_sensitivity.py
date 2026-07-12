#!/usr/bin/env python3
"""Analyze sensitivity of gate outcomes to threshold choices."""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Dict, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cycles-dir", default="output/corepaper_logs/ws4/cycles")
    parser.add_argument("--tau-green-list", default="0.01,0.02,0.04")
    parser.add_argument(
        "--tau-yellow-list",
        default="0.003,0.005,0.01,0.02",
        help="Comma-separated tau_yellow sweep values.",
    )
    parser.add_argument(
        "--tau-yellow",
        type=float,
        default=None,
        help="Deprecated single tau_yellow. If set, overrides tau-yellow-list.",
    )
    parser.add_argument("--output-json", default="output/corepaper_reports/ws5/gate_threshold_sensitivity.json")
    parser.add_argument("--output-md", default="output/corepaper_reports/ws5/gate_threshold_sensitivity.md")
    return parser.parse_args()


def parse_tau_list(raw: str) -> List[float]:
    vals = []
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        vals.append(float(item))
    if not vals:
        raise ValueError("No tau values provided.")
    return vals


def load_cycle_deltas(cycles_dir: pathlib.Path) -> List[Dict]:
    rows: List[Dict] = []
    for path in sorted(cycles_dir.glob("*.json")):
        row = json.loads(path.read_text(encoding="utf-8"))
        if "delta" not in row:
            continue
        rows.append(
            {
                "cycle_id": row.get("cycle_id", path.stem),
                "delta": float(row["delta"]),
            }
        )
    if not rows:
        raise ValueError(f"No cycle delta rows found in {cycles_dir}")
    return rows


def classify(delta: float, tau_green: float, tau_yellow: float) -> str:
    if delta >= tau_green:
        return "green"
    if delta >= tau_yellow:
        return "yellow"
    return "red"


def mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def build_report(rows: List[Dict], tau_values: List[float], tau_yellow_values: List[float]) -> Dict:
    out_rows: List[Dict] = []
    for tau_yellow in tau_yellow_values:
        for tau_green in tau_values:
            if tau_green < tau_yellow:
                continue
            decisions = [classify(r["delta"], tau_green=tau_green, tau_yellow=tau_yellow) for r in rows]
            paired = list(zip(rows, decisions))
            green_deltas = [r["delta"] for r, d in paired if d == "green"]
            yellow_deltas = [r["delta"] for r, d in paired if d == "yellow"]
            red_deltas = [r["delta"] for r, d in paired if d == "red"]
            promoted = [r["delta"] for r, d in paired if d in ("green", "yellow")]
            out_rows.append(
                {
                    "tau_green": tau_green,
                    "tau_yellow": tau_yellow,
                    "n_cycles": len(rows),
                    "green_count": len(green_deltas),
                    "yellow_count": len(yellow_deltas),
                    "red_count": len(red_deltas),
                    "promote_rate_green_only": len(green_deltas) / len(rows),
                    "promote_rate_green_or_yellow": len(promoted) / len(rows),
                    "mean_delta_green_only": mean(green_deltas),
                    "mean_delta_green_or_yellow": mean(promoted),
                    "mean_delta_red": mean(red_deltas),
                }
            )
    return {
        "source_cycles": len(rows),
        "tau_yellow_values": tau_yellow_values,
        "rows": out_rows,
    }


def markdown(payload: Dict, cycles_rows: List[Dict]) -> str:
    lines: List[str] = []
    lines.append("# Gate Threshold Sensitivity (Auto-generated)")
    lines.append("")
    lines.append(f"- Source cycle count: {payload['source_cycles']}")
    lines.append(f"- tau_yellow sweep: {', '.join(f'{v:.4f}' for v in payload['tau_yellow_values'])}")
    lines.append("")
    lines.append("| tau_green | tau_yellow | N | Green | Yellow | Red | Promote (green) | Promote (green+yellow) | Mean Delta (green) | Mean Delta (promoted) |")
    lines.append("|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for row in payload["rows"]:
        lines.append(
            f"| {row['tau_green']:.4f} | {row['tau_yellow']:.4f} | {row['n_cycles']} | {row['green_count']} | {row['yellow_count']} | {row['red_count']} | "
            f"{row['promote_rate_green_only']:.2f} | {row['promote_rate_green_or_yellow']:.2f} | "
            f"{row['mean_delta_green_only']:+.4f} | {row['mean_delta_green_or_yellow']:+.4f} |"
        )
    lines.append("")
    lines.append("## Cycle Inputs")
    lines.append("")
    lines.append("| Cycle | Delta |")
    lines.append("|---|---:|")
    for row in cycles_rows:
        lines.append(f"| {row['cycle_id']} | {row['delta']:+.4f} |")
    return "\n".join(lines).strip() + "\n"


def main() -> int:
    args = parse_args()
    tau_values = parse_tau_list(args.tau_green_list)
    if args.tau_yellow is not None:
        tau_yellow_values = [float(args.tau_yellow)]
    else:
        tau_yellow_values = parse_tau_list(args.tau_yellow_list)
    cycles_dir = pathlib.Path(args.cycles_dir)
    cycle_rows = load_cycle_deltas(cycles_dir)
    payload = build_report(rows=cycle_rows, tau_values=tau_values, tau_yellow_values=tau_yellow_values)

    out_json = pathlib.Path(args.output_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    out_md = pathlib.Path(args.output_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(markdown(payload, cycle_rows), encoding="utf-8")

    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
