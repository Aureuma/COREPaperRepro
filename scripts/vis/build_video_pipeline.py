#!/usr/bin/env python3
"""Run the reproducible supplementary-video pipeline."""

from __future__ import annotations

import argparse
import pathlib
import subprocess


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--external-logs", default="output/corepaper_logs/experiments/external_latest")
    parser.add_argument("--software-transfer-logs", default="output/corepaper_logs/experiments/software_transfer_latest")
    parser.add_argument("--sim2sim-logs", default="output/corepaper_logs/experiments/sim2sim_latest")
    parser.add_argument("--output-dir", default="output/corepaper_assets/video")
    parser.add_argument("--identity", default="config/visual_identity.json")
    parser.add_argument("--submission-dir", default="output/corepaper_submission")
    return parser.parse_args()


def run(cmd: list[str], cwd: pathlib.Path) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


def main() -> int:
    args = parse_args()
    root = pathlib.Path(__file__).resolve().parents[2]

    run(
        [
            "python3",
            "scripts/vis/render_video.py",
            "--external-logs",
            args.external_logs,
            "--software-transfer-logs",
            args.software_transfer_logs,
            "--sim2sim-logs",
            args.sim2sim_logs,
            "--identity",
            args.identity,
            "--output-dir",
            args.output_dir,
            "--submission-dir",
            args.submission_dir,
        ],
        root,
    )
    run(
        [
            "python3",
            "scripts/vis/polish_video.py",
            "--manifest",
            f"{args.output_dir}/manifest.json",
            "--identity",
            args.identity,
            "--output-dir",
            args.output_dir,
            "--submission-dir",
            args.submission_dir,
        ],
        root,
    )

    print("Video pipeline complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
