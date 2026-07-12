#!/usr/bin/env python3
"""Legacy compatibility wrapper for paper figure generation.

Use `scripts/figures/generate_paper_figures.py` directly for new workflows.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys


def main() -> int:
    root = pathlib.Path(__file__).resolve().parents[2]
    script = root / "scripts/figures/generate_paper_figures.py"
    subprocess.run([sys.executable, str(script)], cwd=root, check=True)
    print(
        "Compatibility wrapper: generated paper SVG assets in paper/figures. "
        "Use scripts/figures/generate_paper_figures.py for new workflows."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
