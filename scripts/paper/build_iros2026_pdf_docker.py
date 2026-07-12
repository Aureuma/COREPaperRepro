#!/usr/bin/env python3
"""Dockerized TeX Live 2024 build for the IROS 2026 LaTeX package."""

from __future__ import annotations

import argparse
import os
import pathlib
import subprocess
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("main_tex", nargs="?", default="manuscript.tex")
    parser.add_argument("--image", default=os.environ.get("TEXLIVE_IMAGE", "danteev/texlive:2024-B"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    root_dir = pathlib.Path(__file__).resolve().parents[2]
    tex_dir = root_dir / "paper"
    main_tex = args.main_tex
    doc_basename = pathlib.Path(main_tex).stem
    build_dir = "build"
    tex_source = tex_dir / main_tex

    if not tex_source.is_file():
        print(f"Missing TeX source: {tex_source}", file=sys.stderr)
        return 1

    subprocess.run(
        [sys.executable, "scripts/paper/generate_result_macros.py"],
        cwd=root_dir,
        check=True,
    )

    print(f"Using image: {args.image}")
    subprocess.run(["docker", "pull", args.image], check=True, stdout=subprocess.DEVNULL)

    uid = str(os.getuid())
    gid = str(os.getgid())
    container_cmd = (
        "set -eu\n"
        f"rm -rf {build_dir}\n"
        f"mkdir -p {build_dir}\n"
        f"pdflatex -interaction=nonstopmode -halt-on-error -file-line-error -output-directory={build_dir} {main_tex}\n"
        f"bibtex {build_dir}/{doc_basename}\n"
        f"pdflatex -interaction=nonstopmode -halt-on-error -file-line-error -output-directory={build_dir} {main_tex}\n"
        f"pdflatex -interaction=nonstopmode -halt-on-error -file-line-error -output-directory={build_dir} {main_tex}\n"
    )

    subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "-u",
            f"{uid}:{gid}",
            "-e",
            "HOME=/tmp",
            "-v",
            f"{root_dir}:/work",
            "-w",
            "/work/paper",
            args.image,
            "/bin/sh",
            "-lc",
            container_cmd,
        ],
        check=True,
    )

    built_pdf = tex_dir / build_dir / f"{doc_basename}.pdf"
    print(f"Built PDF: {built_pdf}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
