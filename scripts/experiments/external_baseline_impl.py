#!/usr/bin/env python3
"""Software implementation-backed external baseline wrapper.

This command preserves the prior CLI while delegating scoring to the
deterministic stochastic benchmark model in ``software_benchmark.py``.
"""

from __future__ import annotations

import argparse
import json

from software_benchmark import simulate_score


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--variant", required=True, choices=("ext1", "ext2"))
    parser.add_argument("--seed", type=int, required=True)
    return parser.parse_args()

def main() -> int:
    args = parse_args()
    payload = simulate_score(
        variant=args.variant,
        scenario="nominal",
        seed=args.seed,
        run_id=args.run_id,
    )

    print(
        json.dumps(
            {
                "run_id": args.run_id,
                "seed": args.seed,
                "variant": args.variant,
                "resolved_variant": payload["resolved_variant"],
                "implementation": "software_reference_impl",
                "primary_metric": round(payload["score"], 4),
                "status": "ok",
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
