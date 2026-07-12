#!/usr/bin/env python3
"""Legacy fixed-score command for harness smoke testing only.

Primary benchmark suites use ``software_benchmark.py``.
"""

from __future__ import annotations

import argparse
import json
import time


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--score", type=float, required=True)
    parser.add_argument("--seed", type=int, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    time.sleep(0.05)
    print(
        json.dumps(
            {
                "run_id": args.run_id,
                "seed": args.seed,
                "primary_metric": args.score,
                "status": "ok",
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
