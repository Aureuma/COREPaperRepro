#!/usr/bin/env python3
"""Create a WS4 cycle entry from experiment summary groups."""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary-json", required=True, help="Path to output/corepaper_reports/experiments/summary JSON.")
    parser.add_argument("--cycle-id", required=True, help="Cycle ID to write.")
    parser.add_argument("--hypothesis-id", required=True, help="Hypothesis ID.")
    parser.add_argument("--baseline-group", default="baseline")
    parser.add_argument("--method-group", default="method")
    parser.add_argument("--notes", default="Cycle derived from summarized multiseed experiment output.")
    return parser.parse_args()


def find_group(groups: list[dict], name: str) -> float:
    for group in groups:
        if group.get("group") == name:
            return float(group.get("mean", 0.0))
    raise ValueError(f"Missing group '{name}' in summary.")


def main() -> int:
    args = parse_args()
    payload = json.loads(pathlib.Path(args.summary_json).read_text(encoding="utf-8"))
    groups = payload.get("groups", [])

    baseline = find_group(groups, args.baseline_group)
    method = find_group(groups, args.method_group)

    cmd = [
        sys.executable,
        "scripts/ws4/run_cycle.py",
        "--cycle-id",
        args.cycle_id,
        "--hypothesis-id",
        args.hypothesis_id,
        "--baseline",
        str(baseline),
        "--method",
        str(method),
        "--direction",
        "maximize",
        "--notes",
        args.notes,
    ]
    result = subprocess.run(cmd, check=False)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())

