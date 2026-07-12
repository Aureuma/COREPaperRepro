#!/usr/bin/env python3
"""Validate generated figure assets."""

from __future__ import annotations

import pathlib
import sys
from typing import List


ROOT = pathlib.Path(__file__).resolve().parents[2]


def main() -> int:
    errors: List[str] = []
    required = [
        ROOT / "paper/figures/metaworld_taskwise.svg",
        ROOT / "paper/figures/metaworld_taskwise.pdf",
        ROOT / "paper/figures/recent_baselines_matrix.svg",
        ROOT / "paper/figures/recent_baselines_matrix.pdf",
        ROOT / "paper/figures/custom_diagnostics.svg",
        ROOT / "paper/figures/custom_diagnostics.pdf",
        ROOT / "paper/figures/uncertainty_dominance.svg",
        ROOT / "paper/figures/uncertainty_dominance.pdf",
        ROOT / "paper/figures/gate_timeline.svg",
        ROOT / "paper/figures/gate_timeline.pdf",
        ROOT / "paper/figures/README.md",
    ]
    for path in required:
        if not path.is_file():
            errors.append(f"Missing figure file: {path}")
        elif path.stat().st_size == 0:
            errors.append(f"Empty figure file: {path}")

    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1
    print("Figure assets validation successful.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
