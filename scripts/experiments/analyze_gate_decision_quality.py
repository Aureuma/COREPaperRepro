#!/usr/bin/env python3
"""Evaluate gate decision quality using logged cycle deltas.

This script estimates false-promote and missed-promote rates by comparing
recorded cycle decisions against threshold-derived target decisions from the
observed delta values.
"""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Dict, List


VALID_DECISIONS = {"green", "yellow", "red"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cycles-dir", default="output/corepaper_logs/ws4/cycles")
    parser.add_argument("--tau-green", type=float, default=0.02)
    parser.add_argument("--tau-yellow", type=float, default=0.005)
    parser.add_argument("--output-json", default="output/corepaper_reports/ws5/gate_decision_quality.json")
    parser.add_argument("--output-md", default="output/corepaper_reports/ws5/gate_decision_quality.md")
    return parser.parse_args()


def normalize_decision(raw: str) -> str:
    d = (raw or "").strip().lower()
    if d in VALID_DECISIONS:
        return d
    if d in {"continue_and_scale", "promote"}:
        return "green"
    if d in {"monitor", "hold"}:
        return "yellow"
    if d in {"rollback", "reject"}:
        return "red"
    return "unknown"


def target_decision(delta: float, tau_green: float, tau_yellow: float) -> str:
    if delta >= tau_green:
        return "green"
    if delta >= tau_yellow:
        return "yellow"
    return "red"


def mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def load_cycles(cycles_dir: pathlib.Path) -> List[Dict]:
    rows: List[Dict] = []
    for path in sorted(cycles_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if "delta" not in payload:
            continue
        decision = normalize_decision(str(payload.get("decision", "")))
        if decision not in VALID_DECISIONS:
            continue
        rows.append(
            {
                "cycle_id": str(payload.get("cycle_id", path.stem)),
                "timestamp_utc": str(payload.get("timestamp_utc", "")),
                "delta": float(payload["delta"]),
                "actual_decision": decision,
            }
        )
    if not rows:
        raise ValueError(f"No cycle rows with decision+delta found in {cycles_dir}")
    return rows


def build_confusion(rows: List[Dict], tau_green: float, tau_yellow: float) -> Dict:
    matrix = {
        "green": {"green": 0, "yellow": 0, "red": 0},
        "yellow": {"green": 0, "yellow": 0, "red": 0},
        "red": {"green": 0, "yellow": 0, "red": 0},
    }
    detailed: List[Dict] = []
    false_promote = 0
    severe_false_promote = 0
    missed_promote = 0
    cautious_hold = 0
    delta_abs_errors: List[float] = []

    for row in rows:
        target = target_decision(row["delta"], tau_green=tau_green, tau_yellow=tau_yellow)
        actual = row["actual_decision"]
        matrix[target][actual] += 1

        is_false_promote = (actual == "green") and (target == "red")
        is_severe_false_promote = (actual == "green") and (row["delta"] < 0.0)
        is_missed_promote = (actual == "red") and (target == "green")
        is_cautious_hold = (actual == "yellow") and (target == "green")
        false_promote += int(is_false_promote)
        severe_false_promote += int(is_severe_false_promote)
        missed_promote += int(is_missed_promote)
        cautious_hold += int(is_cautious_hold)

        detailed.append(
            {
                **row,
                "target_decision": target,
                "false_promote": is_false_promote,
                "severe_false_promote": is_severe_false_promote,
                "missed_promote": is_missed_promote,
                "cautious_hold": is_cautious_hold,
            }
        )
        delta_abs_errors.append(abs(row["delta"]))

    n = len(rows)
    return {
        "n_cycles": n,
        "tau_green": tau_green,
        "tau_yellow": tau_yellow,
        "confusion_matrix": matrix,
        "false_promote_count": false_promote,
        "severe_false_promote_count": severe_false_promote,
        "missed_promote_count": missed_promote,
        "cautious_hold_count": cautious_hold,
        "false_promote_rate": false_promote / n,
        "severe_false_promote_rate": severe_false_promote / n,
        "missed_promote_rate": missed_promote / n,
        "cautious_hold_rate": cautious_hold / n,
        "mean_abs_delta": mean(delta_abs_errors),
        "rows": detailed,
    }


def markdown(payload: Dict) -> str:
    lines: List[str] = []
    lines.append("# Gate Decision Quality (Auto-generated)")
    lines.append("")
    lines.append(f"- Cycles analyzed: {payload['n_cycles']}")
    lines.append(f"- tau_green: {payload['tau_green']:.4f}")
    lines.append(f"- tau_yellow: {payload['tau_yellow']:.4f}")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|---|---:|")
    lines.append(f"| False promote count | {payload['false_promote_count']} |")
    lines.append(f"| False promote rate | {payload['false_promote_rate']:.3f} |")
    lines.append(f"| Severe false promote count (delta<0) | {payload['severe_false_promote_count']} |")
    lines.append(f"| Severe false promote rate | {payload['severe_false_promote_rate']:.3f} |")
    lines.append(f"| Missed promote count | {payload['missed_promote_count']} |")
    lines.append(f"| Missed promote rate | {payload['missed_promote_rate']:.3f} |")
    lines.append(f"| Cautious-hold count | {payload['cautious_hold_count']} |")
    lines.append(f"| Cautious-hold rate | {payload['cautious_hold_rate']:.3f} |")
    lines.append("")
    lines.append("## Confusion Matrix (Target vs Actual)")
    lines.append("")
    lines.append("| Target\\\\Actual | green | yellow | red |")
    lines.append("|---|---:|---:|---:|")
    for target in ("green", "yellow", "red"):
        row = payload["confusion_matrix"][target]
        lines.append(f"| {target} | {row['green']} | {row['yellow']} | {row['red']} |")
    lines.append("")
    lines.append("## Cycle Rows")
    lines.append("")
    lines.append("| Cycle | Delta | Target | Actual | False Promote | Missed Promote | Cautious Hold |")
    lines.append("|---|---:|---|---|---|---|---|")
    for row in payload["rows"]:
        lines.append(
            f"| {row['cycle_id']} | {row['delta']:+.4f} | {row['target_decision']} | {row['actual_decision']} | "
            f"{'YES' if row['false_promote'] else 'NO'} | {'YES' if row['missed_promote'] else 'NO'} | "
            f"{'YES' if row['cautious_hold'] else 'NO'} |"
        )
    return "\n".join(lines).strip() + "\n"


def main() -> int:
    args = parse_args()
    if args.tau_yellow > args.tau_green:
        raise SystemExit("tau_yellow must be <= tau_green")

    rows = load_cycles(pathlib.Path(args.cycles_dir))
    payload = build_confusion(rows, tau_green=args.tau_green, tau_yellow=args.tau_yellow)

    out_json = pathlib.Path(args.output_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    out_md = pathlib.Path(args.output_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(markdown(payload), encoding="utf-8")

    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

