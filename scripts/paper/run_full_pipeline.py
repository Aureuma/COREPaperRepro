#!/usr/bin/env python3
"""Single-entrypoint paper pipeline with release-grade checks.

Runs:
1) experiments + report generation,
2) figure generation,
3) LaTeX PDF build,
4) validation + schema sanity checks,
5) critique pass (LLM counsel only, batch-provider mode),
6) automatic semantic-version bump only on successful completion.
"""

from __future__ import annotations

import argparse
import os
import pathlib
import subprocess
import sys
import time
from typing import Sequence


ROOT = pathlib.Path(__file__).resolve().parents[2]
PY = sys.executable
PIPELINE_GEMINI_MODEL = os.getenv(
    "PIPELINE_GEMINI_MODEL",
    os.getenv("COREPAPER_GEMINI_MODEL_NAME", "gemini-3.1-pro-preview"),
)
PIPELINE_GEMINI_SCHEMA_MODE = os.getenv("PIPELINE_GEMINI_SCHEMA_MODE", "compact")
PIPELINE_CLAUDE_MODEL = os.getenv(
    "PIPELINE_CLAUDE_MODEL",
    os.getenv("COREPAPER_BEDROCK_MODEL_ID", "us.anthropic.claude-opus-4-6-v1"),
)
PIPELINE_CLAUDE_BACKEND = os.getenv("PIPELINE_CLAUDE_BACKEND", "boto3")
PIPELINE_CLAUDE_SCHEMA_MODE = os.getenv("PIPELINE_CLAUDE_SCHEMA_MODE", "compact")
PIPELINE_LOCAL_COUNCIL_LABEL = os.getenv("PIPELINE_LOCAL_COUNCIL_LABEL", "codex")
PIPELINE_COUNSEL_IMPROVEMENT_DIRECTIVE = os.getenv("PIPELINE_COUNSEL_IMPROVEMENT_DIRECTIVE", "").strip()
PIPELINE_COUNSEL_MAX_ROUNDS = 5


def _read_env_int(name: str, default: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        return int(raw)
    except ValueError:
        return default


def _read_counsel_rounds(default: int = 5) -> int:
    requested = _read_env_int("PIPELINE_COUNSEL_ROUNDS", default)
    if requested < 1:
        return default
    return min(requested, PIPELINE_COUNSEL_MAX_ROUNDS)


PIPELINE_COUNSEL_ROUNDS = _read_counsel_rounds()


def run(cmd: Sequence[str]) -> None:
    subprocess.run(list(cmd), cwd=ROOT, check=True)


def run_step(name: str, cmd: Sequence[str]) -> None:
    start = time.time()
    print(f"[pipeline] START {name}")
    run(cmd)
    elapsed = time.time() - start
    print(f"[pipeline] DONE  {name} ({elapsed:.1f}s)")


def read_version() -> str:
    return (ROOT / "VERSION").read_text(encoding="utf-8").strip()


def require_artifacts(step: str, artifacts: Sequence[tuple[str, int]]) -> None:
    for rel_path, min_size in artifacts:
        path = ROOT / rel_path
        if not path.is_file():
            raise RuntimeError(f"[pipeline] {step}: missing required artifact: {rel_path}")
        size = path.stat().st_size
        if size < min_size:
            raise RuntimeError(
                f"[pipeline] {step}: artifact too small ({size} bytes < {min_size}): {rel_path}"
            )


def maybe_run_critique_step(name: str, cmd: Sequence[str], *, strict: bool) -> bool:
    try:
        run_step(name, cmd)
        return True
    except subprocess.CalledProcessError as exc:
        if strict:
            raise
        print(
            f"[pipeline] WARN  {name} failed with exit={exc.returncode}; continuing because --strict-critiques is off."
        )
        return False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--no-auto-bump",
        action="store_true",
        help="Disable automatic version bump at the end of a successful run.",
    )
    parser.add_argument(
        "--bump-part",
        choices=("major", "minor", "patch"),
        default="patch",
        help="Version part to bump when auto-bump is enabled.",
    )
    critique_group = parser.add_mutually_exclusive_group()
    critique_group.add_argument(
        "--with-critiques",
        dest="with_critiques",
        action="store_true",
        help="Run Gemini + Claude critique scripts after paper generation (default).",
    )
    critique_group.add_argument(
        "--without-critiques",
        dest="with_critiques",
        action="store_false",
        help="Skip Gemini + Claude critique scripts.",
    )
    parser.add_argument(
        "--strict-critiques",
        action="store_true",
        help="Fail the pipeline if a critique backend fails.",
    )
    parser.add_argument(
        "--skip-lock-refresh",
        action="store_true",
        help="Skip `uv lock` refresh after version bump.",
    )
    parser.set_defaults(with_critiques=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    run_step("version-sync-preflight", [PY, "scripts/version/check_version_sync.py"])
    run_step("experiments-cycle", [PY, "corepaper_tasks.py", "experiments-cycle"])
    require_artifacts(
        "experiments-cycle",
        [
            ("output/corepaper_reports/experiments/summary_latest.json", 200),
            ("output/corepaper_reports/ws3/metaworld_recent_baselines_stats.json", 500),
            ("output/corepaper_reports/ws3/maniskill_proxy_stats.json", 500),
            ("output/corepaper_reports/ws3/cross_embodiment_proxy_stats.json", 500),
            ("output/corepaper_reports/ws3/metaworld_seedexp_latency_method_n30_stats.json", 400),
            ("output/corepaper_reports/ws3/metaworld_seedexp_adaptmanip_method_n30_stats.json", 400),
            ("output/corepaper_reports/ws5/statistical_effects.json", 300),
            ("output/corepaper_reports/ws5/corepaper_external_n14_statistical_effects.json", 300),
            ("output/corepaper_reports/ws5/o2o_proxy_recent.json", 300),
            ("output/corepaper_reports/ws5/o2o_failure_accounting.json", 200),
            ("output/corepaper_reports/ws5/verification_first_diagnostics.json", 300),
            ("output/corepaper_reports/ws5/adversarial_stress_results.json", 300),
            ("output/corepaper_reports/ws5/reliability_floor.json", 100),
            ("output/corepaper_reports/ws5/corepaper_reliability_floor_n14.json", 100),
            ("output/corepaper_reports/ws5/metaworld_cvar_sensitivity_latency_n30.json", 200),
            ("output/corepaper_reports/ws5/metaworld_cvar_sensitivity_adaptmanip_n30.json", 200),
            ("output/corepaper_reports/ws5/metaworld_adapt_equivalence_n14.json", 200),
            ("output/corepaper_reports/ws5/uncertainty_misspec_sensitivity.json", 300),
            ("output/corepaper_reports/ws5/library_parity_official.json", 300),
            ("output/corepaper_reports/ws5/latency_aware_official_parity_audit.json", 200),
        ],
    )
    run_step("figures", [PY, "corepaper_tasks.py", "figures"])
    require_artifacts(
        "figures",
        [
            ("output/corepaper_assets/figures/F1_pipeline.svg", 1000),
            ("output/corepaper_assets/figures/F2_main_benchmark.svg", 1000),
            ("output/corepaper_assets/figures/F3_ablation.svg", 1000),
            ("output/corepaper_assets/figures/F4_robustness.svg", 1000),
            ("output/corepaper_assets/figures/F5_failure_taxonomy.svg", 1000),
            ("output/corepaper_assets/figures/F6_baseline_calibration.svg", 1000),
            ("output/corepaper_assets/figures/F7_metaworld_taskwise.svg", 1000),
        ],
    )
    run_step("build-pdf", [PY, "scripts/paper/build_iros2026_pdf_docker.py"])
    require_artifacts("build-pdf", [("paper/build/manuscript.pdf", 100_000)])
    run_step("validate", [PY, "corepaper_tasks.py", "validate"])
    require_artifacts(
        "validate",
        [
            ("paper/generated/results_macros.tex", 2000),
            ("output/corepaper_reports/version_snapshot.json", 300),
        ],
    )
    run_step("sanity-checks-pre-bump", [PY, "scripts/paper/pipeline_sanity_checks.py", "--label", "pre-bump"])

    if args.with_critiques:
        local_council_rel = "output/corepaper_reports/review_readiness/corepaper_local_council_opinion_latest.json"
        run_step(
            "local-council-opinion",
            [
                PY,
                "scripts/review_readiness/generate_local_council_opinion.py",
                "--paper-tex",
                "paper/manuscript.tex",
                "--plan-md",
                "docs/plan.md",
                "--output-json",
                local_council_rel,
                "--label",
                PIPELINE_LOCAL_COUNCIL_LABEL,
            ],
        )
        require_artifacts("local-council-opinion", [(local_council_rel, 80)])
        counsel_cmd = [
            PY,
            "scripts/review_readiness/run_llm_counsel_critique.py",
            "--gemini-model",
            PIPELINE_GEMINI_MODEL,
            "--gemini-schema-mode",
            PIPELINE_GEMINI_SCHEMA_MODE,
            "--claude-model",
            PIPELINE_CLAUDE_MODEL,
            "--claude-backend",
            PIPELINE_CLAUDE_BACKEND,
            "--claude-schema-mode",
            PIPELINE_CLAUDE_SCHEMA_MODE,
            "--rounds",
            str(PIPELINE_COUNSEL_ROUNDS),
            "--council-local-opinion-json",
            local_council_rel,
            "--council-local-opinion-label",
            PIPELINE_LOCAL_COUNCIL_LABEL,
            "--allow-stale-fallback",
        ]
        if PIPELINE_COUNSEL_IMPROVEMENT_DIRECTIVE:
            counsel_cmd.extend(["--improvement-directive", PIPELINE_COUNSEL_IMPROVEMENT_DIRECTIVE])
        maybe_run_critique_step("llm-counsel-critique", counsel_cmd, strict=args.strict_critiques)

    if not args.no_auto_bump:
        pre_bump_version = read_version()
        run_step(
            f"version-bump-{args.bump_part}",
            [PY, "scripts/version/bump_version.py", "--part", args.bump_part],
        )
        if not args.skip_lock_refresh:
            run_step("uv-lock-refresh", ["uv", "lock"])
        run_step("regenerate-macros", [PY, "scripts/paper/generate_result_macros.py"])
        run_step("version-sync-post-bump", [PY, "scripts/version/check_version_sync.py"])
        run_step("version-snapshot-post-bump", [PY, "scripts/version/write_version_snapshot.py"])
        run_step("sanity-checks-post-bump", [PY, "scripts/paper/pipeline_sanity_checks.py", "--label", "post-bump"])
        post_bump_version = read_version()
        if pre_bump_version == post_bump_version:
            raise RuntimeError(
                "[pipeline] version bump step completed but VERSION did not change; refusing silent success."
            )
        print(f"[pipeline] VERSION {pre_bump_version} -> {post_bump_version}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
