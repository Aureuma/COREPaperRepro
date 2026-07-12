#!/usr/bin/env python3
"""Write a version-linked snapshot of key artifacts for release tracking."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import subprocess
from typing import Dict, List


ROOT = pathlib.Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "output/corepaper_reports/version_snapshot.json"


ARTIFACT_PATHS = [
    "paper/build/manuscript.pdf",
    "paper/generated/results_macros.tex",
    "output/corepaper_reports/ws3/metaworld_slice_stats.json",
    "output/corepaper_reports/ws3/metaworld_recent_baselines_stats.json",
    "output/corepaper_reports/ws3/metaworld_seedexp_ext2_method_stats.json",
    "output/corepaper_reports/ws3/metaworld_seedexp_latency_method_stats.json",
    "output/corepaper_reports/ws3/metaworld_seedexp_adaptmanip_method_stats.json",
    "output/corepaper_reports/ws3/metaworld_seedexp_latency_method_n30_stats.json",
    "output/corepaper_reports/ws3/metaworld_seedexp_adaptmanip_method_n30_stats.json",
    "output/corepaper_reports/ws5/statistical_effects.json",
    "output/corepaper_reports/ws5/reliability_floor.json",
    "output/corepaper_reports/ws5/metaworld_cvar_sensitivity_latency_n30.json",
    "output/corepaper_reports/ws5/metaworld_cvar_sensitivity_adaptmanip_n30.json",
    "output/corepaper_reports/ws5/metaworld_adapt_equivalence_n14.json",
]

LATEST_GLOBS = [
    "output/corepaper_reports/review_readiness/corepaper_gemini_critique_*.json",
    "output/corepaper_reports/review_readiness/corepaper_bedrock_claude_critique_*.json",
    "output/corepaper_reports/review_readiness/corepaper_llm_counsel_critique_*.json",
]


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git_stdout(args: List[str]) -> str:
    proc = subprocess.run(
        ["git"] + args,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return ""
    return (proc.stdout or "").strip()


def read_project_version() -> str:
    version_file = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if not version_file:
        raise SystemExit("VERSION file is empty.")
    return version_file


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Snapshot output path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_path = pathlib.Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    version = read_project_version()
    head = git_stdout(["rev-parse", "HEAD"])
    short_head = git_stdout(["rev-parse", "--short", "HEAD"])
    dirty_lines = git_stdout(["status", "--short"]).splitlines()

    artifacts: List[Dict[str, object]] = []
    resolved_paths = list(ARTIFACT_PATHS)
    for pattern in LATEST_GLOBS:
        matches = sorted(ROOT.glob(pattern))
        if matches:
            resolved_paths.append(str(matches[-1].relative_to(ROOT)))
        else:
            resolved_paths.append(pattern)

    for rel in resolved_paths:
        path = ROOT / rel
        if path.exists():
            artifacts.append(
                {
                    "path": rel,
                    "exists": True,
                    "size_bytes": path.stat().st_size,
                    "sha256": sha256(path),
                }
            )
        else:
            artifacts.append({"path": rel, "exists": False})

    payload: Dict[str, object] = {
        "project": "corepaper",
        "version": version,
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git": {
            "head": head,
            "short_head": short_head,
            "dirty": len(dirty_lines) > 0,
            "dirty_file_count": len(dirty_lines),
        },
        "artifacts": artifacts,
    }

    out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
