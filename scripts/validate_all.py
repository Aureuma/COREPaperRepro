#!/usr/bin/env python3
"""Run the consolidated validation stack."""

from __future__ import annotations

import pathlib
import subprocess
import sys


def run(cmd: list[str], cwd: pathlib.Path) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


def main() -> int:
    root = pathlib.Path(__file__).resolve().parents[1]
    py = sys.executable

    run([py, "scripts/version/check_version_sync.py"], root)
    run([py, "scripts/validate_planning_docs.py"], root)
    run([py, "scripts/paper/generate_result_macros.py"], root)
    run([py, "scripts/experiments/validate_experiment_stack.py"], root)
    run([py, "scripts/experiments/compute_custom_scenario_ci.py"], root)
    run([py, "scripts/experiments/generate_baseline_implementation_details.py"], root)
    run([py, "scripts/experiments/audit_recent_baseline_official_parity.py"], root)
    # Regenerate the anonymous release so bundle validation checks current file names.
    run([py, "scripts/review_readiness/build_anonymous_release.py"], root)
    run([py, "scripts/paper/validate_bundle.py"], root)
    run(
        [
            py,
            "scripts/paper/validate_iros2026_citations.py",
            "--tex",
            "paper/manuscript.tex",
            "--bib",
            "paper/references.bib",
        ],
        root,
    )
    run([py, "scripts/paper/pipeline_sanity_checks.py", "--label", "validate-all"], root)
    run([py, "scripts/version/write_version_snapshot.py"], root)

    print("All consolidated-layout validation checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
