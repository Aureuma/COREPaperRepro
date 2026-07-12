#!/usr/bin/env python3
"""Compute integrity hashes for experiment configs and logs."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
from typing import Dict, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="Experiment suite config path.")
    parser.add_argument("--logs-dir", required=True, help="Experiment logs directory.")
    parser.add_argument("--output", default="output/corepaper_reports/experiments/integrity_report_latest.json")
    return parser.parse_args()


def sha256_of(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    args = parse_args()
    config = pathlib.Path(args.config)
    logs_dir = pathlib.Path(args.logs_dir)
    output = pathlib.Path(args.output)

    files: List[pathlib.Path] = [config]
    files.extend(sorted(logs_dir.glob("*.json")))

    report: Dict[str, object] = {"files": []}
    for path in files:
        if not path.exists():
            continue
        report["files"].append(
            {
                "path": str(path),
                "sha256": sha256_of(path),
                "size_bytes": path.stat().st_size,
            }
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Integrity report written to: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

