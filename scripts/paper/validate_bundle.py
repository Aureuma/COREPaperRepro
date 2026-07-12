#!/usr/bin/env python3
"""Validate submission bundle artifacts."""

from __future__ import annotations

import pathlib
import sys
import zipfile
from typing import List


ROOT = pathlib.Path(__file__).resolve().parents[2]


def main() -> int:
    errors: List[str] = []
    required = [
        ROOT / "output/corepaper_submission/corepaper_main_paper_draft.md",
        ROOT / "output/corepaper_submission/corepaper_main_paper_draft.pdf",
        ROOT / "output/corepaper_submission/corepaper_metadata.yaml",
        ROOT / "output/corepaper_submission/corepaper_supplementary_notes.md",
        ROOT / "output/corepaper_submission/corepaper_checksums.txt",
        ROOT / "output/corepaper_submission/corepaper_submission_bundle.zip",
        ROOT / "output/corepaper_submission/corepaper_video.mp4",
        ROOT / "output/corepaper_submission/corepaper_anonymous_release.zip",
    ]
    for path in required:
        if not path.is_file():
            errors.append(f"Missing bundle file: {path}")
        elif path.stat().st_size == 0:
            errors.append(f"Empty bundle file: {path}")

    anon_zip = ROOT / "output/corepaper_submission/corepaper_anonymous_release.zip"
    if anon_zip.is_file() and anon_zip.stat().st_size > 0:
        try:
            with zipfile.ZipFile(anon_zip) as zf:
                names = set(zf.namelist())
        except zipfile.BadZipFile:
            errors.append(f"Corrupt ZIP archive: {anon_zip}")
        else:
            required_members = [
                "paper/manuscript.tex",
                "paper/generated/results_macros.tex",
                "paper/ieeeconf.cls",
                "paper/references.bib",
                "paper/build/manuscript.pdf",
            ]
            for member in required_members:
                if member not in names:
                    errors.append(f"Anonymous release missing required member: {member}")

    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1
    print("Submission bundle validation successful.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
