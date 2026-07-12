#!/usr/bin/env python3
"""Run one WS4 feedback cycle and update logs."""

from __future__ import annotations

import argparse
import json
import pathlib
from datetime import datetime, timezone
from typing import Dict, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cycle-id", required=True, help="Unique cycle ID, e.g. cycle-001.")
    parser.add_argument("--hypothesis-id", required=True, help="Hypothesis ID, e.g. H1.")
    parser.add_argument("--baseline", required=True, type=float, help="Baseline score.")
    parser.add_argument("--method", required=True, type=float, help="Method score.")
    parser.add_argument(
        "--direction",
        required=True,
        choices=("maximize", "minimize"),
        help="Whether higher or lower metric values are better.",
    )
    parser.add_argument("--notes", default="", help="Optional notes.")
    parser.add_argument("--policy", default="config/feedback_loop_policy.json")
    parser.add_argument("--cycles-dir", default="output/corepaper_logs/ws4/cycles")
    parser.add_argument("--iteration-log", default="docs/ws4/iteration-log.md")
    parser.add_argument("--decision-register", default="docs/ws4/decision-register.md")
    return parser.parse_args()


def load_policy(path: pathlib.Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate_cycle(direction: str, baseline: float, method: float, policy: Dict) -> Tuple[float, str, str]:
    if direction == "maximize":
        delta = method - baseline
    else:
        delta = baseline - method

    thresholds = policy["decision_thresholds"][direction]
    if delta >= thresholds["green_delta"]:
        decision = "green"
    elif delta >= thresholds["yellow_delta"]:
        decision = "yellow"
    else:
        decision = "red"

    action = policy["actions"][decision]
    return delta, decision, action


def severity_for_decision(decision: str) -> str:
    if decision == "red":
        return "high"
    if decision == "yellow":
        return "medium"
    return "low"


def append_markdown_row(path: pathlib.Path, row: str, unique_key: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing_lines = []
    if path.exists():
        existing_lines = path.read_text(encoding="utf-8").splitlines()
    filtered = [line for line in existing_lines if unique_key not in line]
    output_lines = filtered + [row]
    path.write_text("\n".join(output_lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    policy = load_policy(pathlib.Path(args.policy))
    delta, decision, action = evaluate_cycle(args.direction, args.baseline, args.method, policy)

    report = {
        "cycle_id": args.cycle_id,
        "timestamp_utc": now,
        "hypothesis_id": args.hypothesis_id,
        "direction": args.direction,
        "baseline": args.baseline,
        "method": args.method,
        "delta": round(delta, 6),
        "decision": decision,
        "next_action": action,
        "notes": args.notes,
    }

    cycles_dir = pathlib.Path(args.cycles_dir)
    cycles_dir.mkdir(parents=True, exist_ok=True)
    report_path = cycles_dir / f"{args.cycle_id}.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    iteration_row = (
        f"| {args.cycle_id} | {now} | {args.hypothesis_id} | "
        f"{args.baseline:.4f} | {args.method:.4f} | {delta:.4f} | {decision} | {action} |"
    )
    append_markdown_row(pathlib.Path(args.iteration_log), iteration_row, unique_key=f"| {args.cycle_id} |")

    severity = severity_for_decision(decision)
    decision_id = f"D-{args.cycle_id.upper()}"
    rationale = args.notes.replace("|", "/").strip() or f"delta={delta:.4f} under {args.direction} objective"
    decision_row = (
        f"| {decision_id} | {now} | {args.cycle_id} | {severity} | "
        f"{decision}:{action} | {rationale} | TBA |"
    )
    append_markdown_row(pathlib.Path(args.decision_register), decision_row, unique_key=f"| {decision_id} |")

    print(f"Cycle report: {report_path}")
    print(f"Decision: {decision} ({action}), delta={delta:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
