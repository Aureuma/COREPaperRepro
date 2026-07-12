#!/usr/bin/env python3
"""Run reproducibility audit and write Review-Readiness audit report."""

from __future__ import annotations

import argparse
import pathlib
import subprocess
from datetime import datetime, timezone
from typing import List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="docs/review_readiness/repro-audit-report.md")
    return parser.parse_args()


def run_cmd(cmd: str) -> tuple[int, str]:
    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=False)
    tail = "\n".join((proc.stdout + "\n" + proc.stderr).splitlines()[-20:])
    return proc.returncode, tail.strip()


def main() -> int:
    args = parse_args()
    output_path = pathlib.Path(args.output)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    checks: List[tuple[str, str]] = [
        ("Validation Stack", "python3 scripts/validate_all.py"),
        (
            "Experiment Smoke Suite",
            "python3 scripts/experiments/run_harness.py --config config/experiments_smoke.json --output-dir output/corepaper_logs/experiments/latest --clean-output-dir",
        ),
        ("WS4 Cycle Validation", "python3 scripts/ws4/validate_cycles.py --min-cycles 2"),
    ]

    rows = []
    blocking = 0
    non_blocking = 0
    for label, cmd in checks:
        code, tail = run_cmd(cmd)
        status = "Pass" if code == 0 else "Fail"
        if code != 0:
            blocking += 1
        rows.append((label, cmd, "0", str(code), status, tail.replace("|", "/")))

    lines: List[str] = []
    lines.append("# Review-Readiness-03 Reproducibility Audit Report")
    lines.append("")
    lines.append(f"Last updated: {now}")
    lines.append("Owner: TBA")
    lines.append("Status: Active")
    lines.append("")
    lines.append("## Audit Environment")
    lines.append("")
    lines.append("- OS: linux")
    lines.append("- Python/toolchain versions: python3")
    lines.append("- Hardware: local execution environment")
    lines.append("")
    lines.append("## Fresh-Clone Reproduction Results")
    lines.append("")
    lines.append("| Artifact | Command | Expected Output | Observed Output | Pass/Fail | Notes |")
    lines.append("|---|---|---|---|---|---|")
    for label, cmd, expected, observed, status, notes in rows:
        lines.append(f"| {label} | `{cmd}` | {expected} | {observed} | {status} | {notes} |")
    lines.append("")
    lines.append("## Findings")
    lines.append("")
    lines.append(f"- Blocking issues: {blocking}")
    lines.append(f"- Non-blocking issues: {non_blocking}")
    lines.append("- Fixed issues: none in this automated audit run")

    output_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    print(f"Repro audit report written to: {output_path}")
    return 0 if blocking == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
