#!/usr/bin/env python3
"""Generate adversarially composed stress scenarios for robustness evaluation."""

from __future__ import annotations

import argparse
import itertools
import json
import pathlib
from typing import Dict, List


COMPONENTS = ("latency", "dropout", "physics", "sensor", "contact")
LEVELS = (0.0, 0.5, 1.0)
WEIGHTS = {"latency": 0.95, "dropout": 0.90, "physics": 0.88, "sensor": 0.84, "contact": 0.92}
INTERACTIONS = (
    ("latency", "dropout", 0.16),
    ("physics", "sensor", 0.14),
    ("contact", "latency", 0.12),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--top-k", type=int, default=12)
    parser.add_argument(
        "--output-json",
        default="config/benchmarks/experiments_adversarial_stress_generated.json",
    )
    parser.add_argument("--seed-end", type=int, default=8)
    return parser.parse_args()


def adversarial_score(values: Dict[str, float]) -> float:
    base = sum(WEIGHTS[name] * values[name] for name in COMPONENTS)
    bonus = 0.0
    for a, b, w in INTERACTIONS:
        bonus += w * values[a] * values[b]
    return base + bonus


def coverage_matrix(rows: List[Dict]) -> Dict[str, Dict[str, int]]:
    out: Dict[str, Dict[str, int]] = {}
    for name in COMPONENTS:
        bins = {"zero": 0, "mid": 0, "high": 0}
        for row in rows:
            value = float(row["components"].get(name, 0.0))
            if value <= 0.0:
                bins["zero"] += 1
            elif value < 1.0:
                bins["mid"] += 1
            else:
                bins["high"] += 1
        out[name] = bins
    return out


def main() -> int:
    args = parse_args()

    candidates: List[Dict] = []
    for combo in itertools.product(LEVELS, repeat=len(COMPONENTS)):
        values = {name: float(level) for name, level in zip(COMPONENTS, combo)}
        active = sum(1 for v in values.values() if v > 0.0)
        if active < 2:
            continue
        score = adversarial_score(values)
        candidates.append({"components": values, "adversarial_score": score, "active_components": active})

    ranked = sorted(candidates, key=lambda row: row["adversarial_score"], reverse=True)
    selected = ranked[: max(1, args.top_k)]

    scenarios: List[Dict] = []
    for i, row in enumerate(selected, start=1):
        scenario_id = f"ADV-{i:02d}"
        scenarios.append(
            {
                "scenario_id": scenario_id,
                "components": row["components"],
                "adversarial_score": round(float(row["adversarial_score"]), 6),
                "active_components": int(row["active_components"]),
            }
        )

    payload = {
        "suite_name": "ws5-adversarial-composed-shifts",
        "variants": ["baseline", "ext2", "latency_aware", "adaptmanip", "robust_cp", "method"],
        "seeds": list(range(1, int(args.seed_end) + 1)),
        "scenario_components": scenarios,
        "coverage_matrix": coverage_matrix(scenarios),
        "generator": {
            "components": list(COMPONENTS),
            "levels": list(LEVELS),
            "weights": WEIGHTS,
            "interactions": [{"a": a, "b": b, "w": w} for a, b, w in INTERACTIONS],
            "top_k": int(args.top_k),
        },
    }

    out_path = pathlib.Path(args.output_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
