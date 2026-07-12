#!/usr/bin/env python3
"""Run experiment suite from JSON config and store structured logs."""

from __future__ import annotations

import argparse
import json
import pathlib
import shlex
import subprocess
import time
from datetime import datetime, timezone
from typing import Dict, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="Suite config JSON.")
    parser.add_argument("--output-dir", default="output/corepaper_logs/experiments/latest", help="Output log directory.")
    parser.add_argument(
        "--clean-output-dir",
        action="store_true",
        help="Remove prior JSON run logs in output directory before executing suite.",
    )
    return parser.parse_args()


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def safe_name(name: str) -> str:
    return "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in name)


def parse_metric_from_stdout(stdout: str) -> Dict:
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    for line in reversed(lines):
        if line.startswith("{") and line.endswith("}"):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
    return {}


def main() -> int:
    args = parse_args()
    config_path = pathlib.Path(args.config)
    output_dir = pathlib.Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    if args.clean_output_dir:
        for stale in output_dir.glob("*.json"):
            stale.unlink()

    config = json.loads(config_path.read_text(encoding="utf-8"))
    suite_name = config.get("suite_name", "unnamed-suite")
    runs: List[Dict] = config.get("runs", [])
    if not runs:
        raise SystemExit(f"No runs configured in {config_path}")

    run_reports: List[Dict] = []
    suite_start = time.time()

    for run in runs:
        run_id = str(run["id"])
        command = str(run["command"])
        expected_status = int(run.get("expected_status", 0))

        start = time.time()
        started_at = now_utc()
        completed = subprocess.run(command, shell=True, capture_output=True, text=True, check=False)
        ended_at = now_utc()
        duration = time.time() - start

        metric_payload = parse_metric_from_stdout(completed.stdout)
        report = {
            "suite_name": suite_name,
            "run_id": run_id,
            "command": command,
            "started_at_utc": started_at,
            "ended_at_utc": ended_at,
            "duration_seconds": round(duration, 3),
            "return_code": completed.returncode,
            "expected_status": expected_status,
            "status_ok": completed.returncode == expected_status,
            "metric_payload": metric_payload,
            "stdout_tail": "\n".join(completed.stdout.splitlines()[-20:]),
            "stderr_tail": "\n".join(completed.stderr.splitlines()[-20:]),
        }
        run_reports.append(report)

        out_file = output_dir / f"{safe_name(run_id)}.json"
        out_file.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    suite_duration = time.time() - suite_start
    summary = {
        "suite_name": suite_name,
        "config": str(config_path),
        "generated_at_utc": now_utc(),
        "duration_seconds": round(suite_duration, 3),
        "total_runs": len(run_reports),
        "successful_runs": sum(1 for r in run_reports if r["status_ok"]),
        "failed_runs": sum(1 for r in run_reports if not r["status_ok"]),
        "runs": [r["run_id"] for r in run_reports],
    }
    (output_dir / "suite_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print(f"Suite completed: {summary['successful_runs']}/{summary['total_runs']} successful runs.")
    print(f"Logs written to: {output_dir}")
    return 0 if summary["failed_runs"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
