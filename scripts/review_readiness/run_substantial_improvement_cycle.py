#!/usr/bin/env python3
"""Run a 20-round substantial-improvement council loop with per-round commits.

Flow per round:
1) Generate local council seat opinion (codex),
2) Run one batch-only Gemini+Claude counsel round with enhancement directive,
3) Apply recurring feedback edits,
4) Rebuild artifacts (full pipeline only when feedback indicates result/code changes),
5) Append round log and commit changes.
"""

from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
VENV_PY = ROOT / ".venv/bin/python"
PY = str(VENV_PY) if VENV_PY.is_file() else sys.executable
DEFAULT_OUTPUT_DIR = Path("output/corepaper_reports/review_readiness")
DEFAULT_IMPROVEMENT_DIRECTIVE = (
    "Propose substantial, reviewer-facing improvements to maximize review robustness. "
    "Prioritize theory rigor and proof correctness, claim-evidence alignment, text flow, "
    "figure/table density and clarity, reproducibility evidence, and concrete edits that can be "
    "implemented immediately in this repository."
)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _run(
    cmd: list[str],
    *,
    use_credentials: bool = False,
    log_path: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    if use_credentials:
        rendered = " ".join(shlex.quote(x) for x in cmd)
        call = ["bash", "-lc", f"source credentials.sh >/dev/null 2>&1 && {rendered}"]
    else:
        call = cmd
    proc = subprocess.run(
        call,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if log_path is not None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        lines = [f"$ {' '.join(call)}"]
        if proc.stdout:
            lines.append("\n[stdout]\n" + proc.stdout)
        if proc.stderr:
            lines.append("\n[stderr]\n" + proc.stderr)
        log_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    if proc.returncode != 0:
        raise RuntimeError(
            f"Command failed (exit={proc.returncode}): {' '.join(call)}\n"
            f"stdout:\n{proc.stdout}\n\nstderr:\n{proc.stderr}"
        )
    return proc


def _git_changed_files() -> list[str]:
    proc = _run(["git", "status", "--porcelain"])
    files: list[str] = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        files.append(line[3:].strip())
    return files


def _append_round_log(
    *,
    log_md: Path,
    round_index: int,
    round_tag: str,
    council_json: Path,
    risk: Any,
    verdict: str,
    pipeline_mode: str,
    committed: bool,
    actions: list[str],
) -> None:
    header = [
        "# Substantial Improvement Council (20 rounds)",
        "",
        "| Round | Tag | Risk | Verdict | Pipeline | Commit | Counsel Artifact | Top Actions |",
        "|---|---|---:|---|---|---|---|---|",
    ]
    if log_md.exists():
        lines = log_md.read_text(encoding="utf-8").splitlines()
        if lines and lines[0].startswith("# Substantial Improvement Council"):
            header = []
    top_actions = "; ".join(actions[:2]) if actions else "none"
    row = (
        f"| {round_index:02d} | `{round_tag}` | `{risk}` | {verdict} | "
        f"`{pipeline_mode}` | `{str(committed).lower()}` | `{council_json}` | {top_actions} |"
    )
    body: list[str] = []
    if header:
        body.extend(header)
    if log_md.exists():
        existing = log_md.read_text(encoding="utf-8").splitlines()
        existing = [ln for ln in existing if not ln.startswith(f"| {round_index:02d} |")]
        if header:
            existing = [ln for ln in existing if ln not in header]
        body.extend(existing)
    body.append(row)
    log_md.parent.mkdir(parents=True, exist_ok=True)
    log_md.write_text("\n".join(body).strip() + "\n", encoding="utf-8")


def _latest_council_json(output_dir: Path, round_tag: str) -> Path:
    pattern = str(output_dir / f"corepaper_llm_counsel_critique_*_{round_tag}.json")
    matches = sorted(glob.glob(pattern))
    if matches:
        return Path(matches[-1])
    fallback_pattern = str(output_dir / f"corepaper_llm_counsel_critique_*_{round_tag}_fallback.json")
    fallback_matches = sorted(glob.glob(fallback_pattern))
    if fallback_matches:
        return Path(fallback_matches[-1])
    raise FileNotFoundError(f"No counsel JSON found for tag={round_tag} in {output_dir}")


def _should_run_full_pipeline(council: dict[str, Any], changed_files: list[str]) -> bool:
    _ = council  # Reserved for future rule expansion; changed-files gate is authoritative.
    for path in changed_files:
        if path.startswith("scripts/experiments/") or path.startswith("config/benchmarks/"):
            return True
        if path in {
            "scripts/paper/generate_result_macros.py",
            "corepaper_tasks.py",
            "scripts/paper/run_full_pipeline.py",
        }:
            return True
    return False


def _commit_round(round_index: int, round_tag: str, council_path: Path, pipeline_mode: str, risk: Any) -> bool:
    changed = _git_changed_files()
    if not changed:
        return False
    _run(["git", "add", "-A"])
    title = f"feat(council): apply substantial-improvement round {round_index:02d}"
    body = (
        f"Round tag: {round_tag}\n"
        f"Counsel artifact: {council_path}\n"
        f"Pipeline mode: {pipeline_mode}\n"
        f"Final risk score: {risk}\n"
    )
    _run(["git", "commit", "-m", title, "-m", body])
    return True


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rounds", type=int, default=20)
    ap.add_argument("--start-round", type=int, default=1)
    ap.add_argument("--tag-prefix", default="substantial20")
    ap.add_argument("--paper-pdf", type=Path, default=Path("paper/build/manuscript.pdf"))
    ap.add_argument("--paper-tex", type=Path, default=Path("paper/manuscript.tex"))
    ap.add_argument("--plan-md", type=Path, default=Path("docs/plan.md"))
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    ap.add_argument("--gemini-model", default="gemini-3.1-pro-preview")
    ap.add_argument("--claude-model", default="us.anthropic.claude-opus-4-6-v1")
    ap.add_argument("--claude-backend", choices=("auto", "si", "boto3"), default="boto3")
    ap.add_argument("--gemini-schema-mode", choices=("full", "compact"), default="compact")
    ap.add_argument("--claude-schema-mode", choices=("full", "compact"), default="compact")
    ap.add_argument("--improvement-directive", default=DEFAULT_IMPROVEMENT_DIRECTIVE)
    ap.add_argument(
        "--allow-stale-fallback",
        action="store_true",
        help="Allow stale provider fallback in counsel if a live provider call fails.",
    )
    ap.add_argument("--local-label", default="codex")
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    if args.rounds < 1:
        print("--rounds must be >= 1", file=sys.stderr)
        return 2
    if args.start_round < 1 or args.start_round > args.rounds:
        print("--start-round must satisfy 1 <= start-round <= rounds", file=sys.stderr)
        return 2
    for req in (args.paper_tex, args.plan_md):
        if not req.exists():
            print(f"Missing required file: {req}", file=sys.stderr)
            return 2
    args.output_dir.mkdir(parents=True, exist_ok=True)
    round_log = args.output_dir / "substantial20_round_log.md"

    # Ensure a current PDF exists before the first council round.
    if not args.paper_pdf.exists():
        _run(["uv", "run", "python", "scripts/paper/build_iros2026_pdf_docker.py"], use_credentials=True)
        _run(["uv", "run", "python", "corepaper_tasks.py", "validate"], use_credentials=True)

    for round_index in range(args.start_round, args.rounds + 1):
        round_tag = f"{args.tag_prefix}-r{round_index:02d}"
        print(f"[improve20] round {round_index}/{args.rounds} tag={round_tag}", flush=True)

        local_json = args.output_dir / f"corepaper_local_council_opinion_{round_tag}.json"
        _run(
            [
                PY,
                "scripts/review_readiness/generate_local_council_opinion.py",
                "--paper-tex",
                str(args.paper_tex),
                "--plan-md",
                str(args.plan_md),
                "--output-json",
                str(local_json),
                "--label",
                args.local_label,
            ],
            log_path=args.output_dir / f"{round_tag}_local.log",
        )

        counsel_cmd = [
            PY,
            "scripts/review_readiness/run_llm_counsel_critique.py",
            "--paper-pdf",
            str(args.paper_pdf),
            "--paper-tex",
            str(args.paper_tex),
            "--plan-md",
            str(args.plan_md),
            "--rounds",
            "1",
            "--tag",
            round_tag,
            "--gemini-model",
            args.gemini_model,
            "--gemini-schema-mode",
            args.gemini_schema_mode,
            "--gemini-max-tex-chars",
            "90000",
            "--gemini-max-plan-chars",
            "60000",
            "--claude-model",
            args.claude_model,
            "--claude-backend",
            args.claude_backend,
            "--claude-schema-mode",
            args.claude_schema_mode,
            "--council-local-opinion-json",
            str(local_json),
            "--council-local-opinion-label",
            args.local_label,
            "--improvement-directive",
            args.improvement_directive,
        ]
        if args.allow_stale_fallback:
            counsel_cmd.append("--allow-stale-fallback")

        _run(
            counsel_cmd,
            use_credentials=True,
            log_path=args.output_dir / f"{round_tag}_counsel.log",
        )

        council_json = _latest_council_json(args.output_dir, round_tag)
        council = _read_json(council_json)

        apply_proc = _run(
            [
                PY,
                "scripts/review_readiness/apply_council_round_feedback.py",
                "--council-json",
                str(council_json),
                "--paper-tex",
                str(args.paper_tex),
                "--fig-script",
                "scripts/figures/generate_paper_figures.py",
            ],
            log_path=args.output_dir / f"{round_tag}_apply.log",
        )
        apply_payload: dict[str, Any] = {}
        try:
            apply_payload = json.loads(apply_proc.stdout.strip() or "{}")
        except json.JSONDecodeError:
            apply_payload = {}

        changed_files = _git_changed_files()
        run_full = _should_run_full_pipeline(council, changed_files)
        if run_full:
            _run(
                [
                    "uv",
                    "run",
                    "python",
                    "scripts/paper/run_full_pipeline.py",
                    "--without-critiques",
                    "--no-auto-bump",
                ],
                use_credentials=True,
                log_path=args.output_dir / f"{round_tag}_pipeline.log",
            )
            pipeline_mode = "full-no-critiques"
        else:
            if bool(apply_payload.get("changed_fig_script")):
                _run(
                    ["uv", "run", "python", "corepaper_tasks.py", "figures"],
                    use_credentials=True,
                    log_path=args.output_dir / f"{round_tag}_figures.log",
                )
            _run(
                ["uv", "run", "python", "scripts/paper/build_iros2026_pdf_docker.py"],
                use_credentials=True,
                log_path=args.output_dir / f"{round_tag}_pdf.log",
            )
            _run(
                ["uv", "run", "python", "corepaper_tasks.py", "validate"],
                use_credentials=True,
                log_path=args.output_dir / f"{round_tag}_validate.log",
            )
            pipeline_mode = "pdf-validate"

        risk = council.get("final_acceptance_risk_score_0_to_10")
        verdict = str(council.get("final_overall_verdict", "N/A"))
        actions = council.get("consensus_actions", [])
        if not isinstance(actions, list):
            actions = []

        pending_changes = bool(_git_changed_files())
        committed = pending_changes
        _append_round_log(
            log_md=round_log,
            round_index=round_index,
            round_tag=round_tag,
            council_json=council_json,
            risk=risk,
            verdict=verdict,
            pipeline_mode=pipeline_mode,
            committed=committed,
            actions=[str(x) for x in actions if isinstance(x, str)],
        )
        if pending_changes or round_log.as_posix() in _git_changed_files():
            _commit_round(round_index, round_tag, council_json, pipeline_mode, risk)

    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[improve20] completed {args.rounds} rounds at {stamp}")
    print(f"[improve20] round log: {round_log}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
