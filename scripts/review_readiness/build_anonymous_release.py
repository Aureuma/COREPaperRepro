#!/usr/bin/env python3
"""Build an anonymized release package for reviewer-facing reproducibility checks."""

from __future__ import annotations

import argparse
import pathlib
import shutil
import tempfile
import zipfile
from typing import List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-zip", default="output/corepaper_submission/corepaper_anonymous_release.zip")
    return parser.parse_args()


def copy_path(src_root: pathlib.Path, rel_path: str, dst_root: pathlib.Path) -> None:
    src = src_root / rel_path
    dst = dst_root / rel_path
    if src.is_dir():
        shutil.copytree(src, dst, dirs_exist_ok=True)
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def build_zip(root: pathlib.Path, src_dir: pathlib.Path, out_zip: pathlib.Path) -> None:
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(src_dir.rglob("*")):
            if path.is_file():
                arcname = path.relative_to(src_dir)
                zf.write(path, arcname=str(arcname))


def main() -> int:
    args = parse_args()
    root = pathlib.Path(__file__).resolve().parents[2]
    out_zip = root / args.output_zip

    include_paths: List[str] = [
        "README.md",
        "pyproject.toml",
        "corepaper_tasks.py",
        "config",
        "scripts/experiments",
        "scripts/figures",
        "scripts/paper",
        "scripts/ws4",
        "scripts/ws5",
        "scripts/review_readiness",
        "scripts/vis",
        "docs/plan.md",
        "docs/ws3/baseline-replication-report.md",
        "docs/ws3/baseline-calibration-note.md",
        "docs/ws5/software-validation-log.md",
        "docs/ws5/sim2sim-validation-log.md",
        "docs/ws6/claim-evidence-matrix.md",
        "docs/review_readiness/repro-audit-report.md",
        "docs/ws8/video-storyboard.md",
        "docs/ws8/media-production-log.md",
        "output/corepaper_reports/experiments",
        "output/corepaper_reports/ws3",
        "output/corepaper_reports/ws5",
        "paper/manuscript.tex",
        "paper/generated/results_macros.tex",
        "paper/ieeeconf.cls",
        "paper/references.bib",
        "paper/figures",
        "output/corepaper_assets/video",
        "paper/build/manuscript.pdf",
        "output/corepaper_submission/corepaper_video.mp4",
        "site/index.html",
    ]

    with tempfile.TemporaryDirectory(prefix="corepaper-anon-") as tmp:
        stage = pathlib.Path(tmp) / "anonymous_release"
        stage.mkdir(parents=True, exist_ok=True)
        for rel in include_paths:
            src = root / rel
            if not src.exists():
                continue
            copy_path(root, rel, stage)

        readme = stage / "ANONYMOUS_RELEASE_README.md"
        readme.write_text(
            "\n".join(
                [
                    "# Anonymous Release Package",
                    "",
                    "This package excludes author identities and contains reproducibility assets for review.",
                    "",
                    "Key entry points:",
                    "- `paper/build/manuscript.pdf`",
                    "- `docs/plan.md`",
                    "- `output/corepaper_reports/ws3/baseline_calibration.md`",
                    "- `output/corepaper_reports/ws5/sim2sim_transfer_results.md`",
                    "- `output/corepaper_submission/corepaper_video.mp4`",
                    "- `site/index.html`",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        build_zip(root, stage, out_zip)

    print(f"Built {out_zip}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
