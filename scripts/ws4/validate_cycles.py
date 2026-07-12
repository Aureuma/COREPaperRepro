#!/usr/bin/env python3
"""Validate WS4 cycle execution artifacts."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cycles-dir", default="output/corepaper_logs/ws4/cycles")
    parser.add_argument("--iteration-log", default="docs/ws4/iteration-log.md")
    parser.add_argument("--decision-register", default="docs/ws4/decision-register.md")
    parser.add_argument("--min-cycles", type=int, default=2)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cycles_dir = pathlib.Path(args.cycles_dir)
    iteration_log = pathlib.Path(args.iteration_log)
    decision_register = pathlib.Path(args.decision_register)
    prioritization_board = pathlib.Path("docs/ws4/prioritization-board.md")
    theory_sync_log = pathlib.Path("docs/ws4/theory-sync-log.md")
    writing_sync_log = pathlib.Path("docs/ws4/writing-sync-log.md")

    errors: List[str] = []

    if not cycles_dir.exists():
        errors.append(f"Missing cycles dir: {cycles_dir}")
    else:
        cycle_files = sorted(cycles_dir.glob("*.json"))
        if len(cycle_files) < args.min_cycles:
            errors.append(f"Expected at least {args.min_cycles} cycle files, found {len(cycle_files)}")
        for path in cycle_files:
            payload = json.loads(path.read_text(encoding="utf-8"))
            for key in ("cycle_id", "hypothesis_id", "baseline", "method", "delta", "decision", "next_action"):
                if key not in payload:
                    errors.append(f"{path} missing key: {key}")
            if payload.get("decision") not in {"green", "yellow", "red"}:
                errors.append(f"{path} has invalid decision: {payload.get('decision')}")

    if not iteration_log.exists():
        errors.append(f"Missing iteration log: {iteration_log}")
    if not decision_register.exists():
        errors.append(f"Missing decision register: {decision_register}")
    if not prioritization_board.exists():
        errors.append(f"Missing prioritization board: {prioritization_board}")
    if not theory_sync_log.exists():
        errors.append(f"Missing theory sync log: {theory_sync_log}")
    if not writing_sync_log.exists():
        errors.append(f"Missing writing sync log: {writing_sync_log}")

    if not errors:
        log_content = iteration_log.read_text(encoding="utf-8")
        reg_content = decision_register.read_text(encoding="utf-8")
        for path in sorted(cycles_dir.glob("*.json")):
            cycle_id = json.loads(path.read_text(encoding="utf-8"))["cycle_id"]
            if cycle_id not in log_content:
                errors.append(f"Iteration log missing cycle: {cycle_id}")
            if cycle_id not in reg_content:
                errors.append(f"Decision register missing cycle: {cycle_id}")

    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1

    print("WS4 cycle validation successful.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
