#!/usr/bin/env python3
"""Export manuscript SVG figures to vector PDF (and optional PNG copies)."""

from __future__ import annotations

import argparse
import pathlib
import sys
from typing import List

import cairosvg


ROOT = pathlib.Path(__file__).resolve().parents[2]
FIG_DIR = ROOT / "paper/figures"
PNG_OUT_DIR = ROOT / "output/corepaper_assets/figures"
LEGACY_SVG_DIR = ROOT / "output/corepaper_assets/figures"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--with-png",
        action="store_true",
        help="Also export PNG copies for web previews under output/corepaper_assets/figures.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    svg_paths = sorted(FIG_DIR.glob("*.svg"))
    if not svg_paths:
        print(f"No SVG files found under {FIG_DIR}", file=sys.stderr)
        return 1

    errors: List[str] = []
    PNG_OUT_DIR.mkdir(parents=True, exist_ok=True)
    for svg_path in svg_paths:
        pdf_path = svg_path.with_suffix(".pdf")
        try:
            cairosvg.svg2pdf(url=str(svg_path), write_to=str(pdf_path))
        except Exception as exc:  # pragma: no cover - defensive path
            errors.append(f"{svg_path.name} -> PDF: {exc}")

        if args.with_png:
            png_path = PNG_OUT_DIR / f"{svg_path.stem}.png"
            try:
                cairosvg.svg2png(url=str(svg_path), write_to=str(png_path))
            except Exception as exc:  # pragma: no cover - defensive path
                errors.append(f"{svg_path.name} -> PNG: {exc}")

    if errors:
        print("Figure export failed for one or more files:", file=sys.stderr)
        for err in errors:
            print(f"- {err}", file=sys.stderr)
        return 1

    print(f"Exported {len(svg_paths)} PDF figure files in {FIG_DIR}")
    if args.with_png:
        print(f"Exported {len(svg_paths)} PNG preview files in {PNG_OUT_DIR}")
        legacy_svgs = sorted(LEGACY_SVG_DIR.glob("F*.svg"))
        legacy_errors: List[str] = []
        for svg_path in legacy_svgs:
            png_path = LEGACY_SVG_DIR / f"{svg_path.stem}.png"
            try:
                cairosvg.svg2png(url=str(svg_path), write_to=str(png_path))
            except Exception as exc:  # pragma: no cover - defensive path
                legacy_errors.append(f"{svg_path.name} -> PNG: {exc}")
        if legacy_errors:
            print("Legacy PNG export failed for one or more files:", file=sys.stderr)
            for err in legacy_errors:
                print(f"- {err}", file=sys.stderr)
            return 1
        if legacy_svgs:
            print(f"Exported {len(legacy_svgs)} legacy PNG preview files in {LEGACY_SVG_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
