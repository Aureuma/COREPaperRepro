#!/usr/bin/env python3
"""Build a draft submission bundle with checksums and archive."""

from __future__ import annotations

import argparse
import hashlib
import pathlib
import zipfile
from typing import List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle-dir", default="output/corepaper_submission")
    return parser.parse_args()


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def write_if_missing(path: pathlib.Path, content: str) -> None:
    if not path.exists():
        path.write_text(content, encoding="utf-8")


def main() -> int:
    args = parse_args()
    bundle_dir = pathlib.Path(args.bundle_dir)
    bundle_dir.mkdir(parents=True, exist_ok=True)

    metadata = bundle_dir / "corepaper_metadata.yaml"
    write_if_missing(
        metadata,
        "\n".join(
            [
                "title: CORE: Closed-Loop Research Operations for Robust Contact-Rich Manipulation",
                "authors:",
                "  - name: TBA",
                "keywords: [robotics, robustness, manipulation, reproducibility]",
                "conference: IROS 2026",
            ]
        )
        + "\n",
    )

    supplementary = bundle_dir / "corepaper_supplementary_notes.md"
    write_if_missing(
        supplementary,
        "\n".join(
            [
                "# Supplementary Notes",
                "",
                "- Robustness and ablation reports are linked in `output/corepaper_reports/ws5/`.",
                "- Reproducibility audit is in `docs/review_readiness/repro-audit-report.md`.",
            ]
        )
        + "\n",
    )

    receipt = bundle_dir / "corepaper_submission_receipt_dry_run.txt"
    write_if_missing(
        receipt,
        "Dry-run preflight receipt generated locally. Replace with official portal receipt at submission time.\n",
    )

    files = [
        bundle_dir / "corepaper_main_paper_draft.md",
        bundle_dir / "corepaper_main_paper_draft.pdf",
        bundle_dir / "corepaper_video.mp4",
        metadata,
        supplementary,
        receipt,
        pathlib.Path("docs/review_readiness/repro-audit-report.md"),
        pathlib.Path("output/corepaper_reports/ws5/robustness_results.md"),
        pathlib.Path("output/corepaper_reports/ws5/ablation_results.md"),
    ]
    existing = [f for f in files if f.exists()]

    checksums = bundle_dir / "corepaper_checksums.txt"
    lines: List[str] = []
    for file in existing:
        lines.append(f"{sha256(file)}  {file.as_posix()}")
    checksums.write_text("\n".join(lines) + "\n", encoding="utf-8")

    archive = bundle_dir / "corepaper_submission_bundle.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file in existing + [checksums]:
            zf.write(file, arcname=file.as_posix())

    print(f"Wrote {checksums}")
    print(f"Wrote {archive}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
