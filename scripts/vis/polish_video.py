#!/usr/bin/env python3
"""Build polished MP4 video assets from the base clip manifest using visual identity tokens."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import subprocess
from dataclasses import dataclass
from typing import Dict, List, Optional


ROOT = pathlib.Path(__file__).resolve().parents[2]
FFMPEG_DOCKER_IMAGE = "lscr.io/linuxserver/ffmpeg:latest"


@dataclass
class ScenarioRow:
    scenario: str
    available_variants: List[str]
    baseline_mean: Optional[float]
    ext2_mean: Optional[float]
    adaptmanip_mean: Optional[float]
    method_mean: Optional[float]
    delta: Optional[float]
    delta_vs_ext2: Optional[float]
    clip: pathlib.Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default="output/corepaper_assets/video/manifest.json")
    parser.add_argument("--identity", default="config/visual_identity.json")
    parser.add_argument("--output-dir", default="output/corepaper_assets/video")
    parser.add_argument("--submission-dir", default="output/corepaper_submission")
    parser.add_argument("--scenario-order", default="META-shifted,S1-hard,S2-med,S3-severe,SIM-isaac")
    parser.add_argument("--crf", type=int, default=22)
    return parser.parse_args()


def resolve_path(path: str) -> pathlib.Path:
    p = pathlib.Path(path)
    if p.is_absolute():
        return p
    return (ROOT / p).resolve()


def rel(path: pathlib.Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def load_json(path: pathlib.Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def ffmpeg_binary() -> List[str]:
    if shutil.which("ffmpeg") is not None:
        return ["ffmpeg"]
    return [
        "docker",
        "run",
        "--rm",
        "-u",
        f"{os.getuid()}:{os.getgid()}",
        "--entrypoint",
        "ffmpeg",
        "-v",
        f"{ROOT.resolve()}:/work",
        "-w",
        "/work",
        FFMPEG_DOCKER_IMAGE,
    ]


def run_ffmpeg(args: List[str]) -> None:
    cmd = ffmpeg_binary() + args
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip() or "unknown ffmpeg failure"
        raise RuntimeError(f"ffmpeg command failed: {' '.join(cmd)}\n{detail}")


def ffmpeg_color(hex_color: str, alpha: float | None = None) -> str:
    base = f"0x{hex_color.lstrip('#')}"
    if alpha is None:
        return base
    return f"{base}@{alpha:.2f}"


def escape_text(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace(":", r"\:")
        .replace("'", r"\'")
        .replace(",", r"\,")
        .replace("|", r"\|")
        .replace("%", r"\%")
        .replace("[", r"\[")
        .replace("]", r"\]")
        .replace("-", r"\-")
    )


def drawtext(*, fontfile: str, text: str, x: int, y: int, size: int, color: str) -> str:
    return (
        "drawtext="
        f"fontfile={fontfile}:"
        f"text='{escape_text(text)}':"
        f"x={x}:y={y}:"
        f"fontsize={size}:"
        f"fontcolor={color}"
    )


def scenario_title(raw: str) -> str:
    mapping = {
        "META-shifted": "MetaWorld Shifted Benchmark",
        "S1-hard": "S1 Hard Shift",
        "S2-med": "S2 Medium Shift",
        "S3-severe": "S3 Severe Shift",
        "SIM-isaac": "Sim2Sim: Isaac Target",
        "SIM-mujoco": "Sim2Sim: MuJoCo Target",
    }
    return mapping.get(raw, raw.replace("-", " "))


def scenario_subtitle(raw: str) -> str:
    mapping = {
        "META-shifted": "Shifted benchmark slice (task-aggregated).",
        "S1-hard": "Software transfer stress slice with hard perturbations.",
        "S2-med": "Software transfer slice with medium perturbations.",
        "S3-severe": "Software transfer slice with severe perturbations.",
        "SIM-isaac": "Cross-engine transfer slice from MuJoCo to Isaac.",
        "SIM-mujoco": "Cross-engine transfer slice from Isaac to MuJoCo.",
    }
    return mapping.get(raw, "Shifted scenario slice with matched evaluation protocol.")


def variant_label(variant: str) -> str:
    mapping = {
        "baseline": "Baseline",
        "ext1": "TRPO-U",
        "ext2": "PPO-CVaR",
        "adaptmanip": "adaptmanip",
        "method": "CORE",
    }
    return mapping.get(variant, variant)


def remove_legacy_gifs(*roots: pathlib.Path) -> int:
    removed = 0
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*.gif"):
            path.unlink(missing_ok=True)
            removed += 1
    return removed


def create_intro_card(
    *,
    out_path: pathlib.Path,
    width: int,
    height: int,
    fps: int,
    seconds: float,
    crf: int,
    colors: Dict[str, str],
    fonts: Dict[str, str],
) -> None:
    vf = ",".join(
        [
            f"drawbox=x=76:y=96:w={width - 152}:h={height - 188}:color={ffmpeg_color(colors['bg_panel'])}:t=fill",
            f"drawbox=x=76:y=96:w={width - 152}:h={height - 188}:color={ffmpeg_color(colors['ink_primary'], 0.28)}:t=4",
            drawtext(
                fontfile=fonts["font_bold"],
                text="CORE: Robustness Under Distribution Shift",
                x=116,
                y=190,
                size=44,
                color=ffmpeg_color(colors["ink_primary"]),
            ),
            drawtext(
                fontfile=fonts["font_regular"],
                text="IROS 2026 Supplementary Video",
                x=116,
                y=258,
                size=30,
                color=ffmpeg_color(colors["ink_secondary"]),
            ),
            drawtext(
                fontfile=fonts["font_regular"],
                text="Paper-aligned slices: shifted benchmark + transfer scenarios",
                x=116,
                y=312,
                size=24,
                color=ffmpeg_color(colors["ink_secondary"]),
            ),
            drawtext(
                fontfile=fonts["font_regular"],
                text="Comparators shown where available: Baseline, PPO-CVaR, adaptmanip, CORE",
                x=116,
                y=364,
                size=22,
                color=ffmpeg_color(colors["ink_secondary"]),
            ),
        ]
    )
    run_ffmpeg(
        [
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c={ffmpeg_color(colors['bg_canvas'])}:s={width}x{height}:d={seconds}",
            "-vf",
            vf,
            "-r",
            str(fps),
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            str(crf),
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            rel(out_path),
        ]
    )


def create_outro_card(
    *,
    out_path: pathlib.Path,
    width: int,
    height: int,
    fps: int,
    seconds: float,
    crf: int,
    colors: Dict[str, str],
    fonts: Dict[str, str],
) -> None:
    vf = ",".join(
        [
            f"drawbox=x=76:y=96:w={width - 152}:h={height - 188}:color={ffmpeg_color(colors['bg_panel'])}:t=fill",
            f"drawbox=x=76:y=96:w={width - 152}:h={height - 188}:color={ffmpeg_color(colors['ink_primary'], 0.28)}:t=4",
            drawtext(
                fontfile=fonts["font_bold"],
                text="CORE Summary",
                x=120,
                y=200,
                size=44,
                color=ffmpeg_color(colors["ink_primary"]),
            ),
            drawtext(
                fontfile=fonts["font_regular"],
                text="Across shifted slices shown here, CORE keeps stronger floors and stability.",
                x=120,
                y=284,
                size=24,
                color=ffmpeg_color(colors["ink_secondary"]),
            ),
            drawtext(
                fontfile=fonts["font_regular"],
                text="See paper figures/tables for full statistics and uncertainty diagnostics.",
                x=120,
                y=336,
                size=24,
                color=ffmpeg_color(colors["ink_secondary"]),
            ),
        ]
    )
    run_ffmpeg(
        [
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c={ffmpeg_color(colors['bg_canvas'])}:s={width}x{height}:d={seconds}",
            "-vf",
            vf,
            "-r",
            str(fps),
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            str(crf),
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            rel(out_path),
        ]
    )


def build_metric_lines(row: ScenarioRow) -> tuple[str, str]:
    score_parts: List[str] = []
    if row.baseline_mean is not None:
        score_parts.append(f"Baseline {row.baseline_mean:.3f}")
    if row.ext2_mean is not None:
        score_parts.append(f"PPO-CVaR {row.ext2_mean:.3f}")
    if row.adaptmanip_mean is not None:
        score_parts.append(f"adaptmanip {row.adaptmanip_mean:.3f}")
    if row.method_mean is not None:
        score_parts.append(f"CORE {row.method_mean:.3f}")
    deltas: List[str] = []
    if row.delta is not None:
        deltas.append(f"CORE-Baseline {row.delta:+.3f}")
    if row.delta_vs_ext2 is not None:
        deltas.append(f"CORE-PPO-CVaR {row.delta_vs_ext2:+.3f}")
    score_line = "Scores: " + " | ".join(score_parts) if score_parts else ""
    delta_line = "Deltas: " + " | ".join(deltas) if deltas else ""
    return score_line, delta_line


def create_scenario_segment(
    *,
    row: ScenarioRow,
    out_path: pathlib.Path,
    width: int,
    height: int,
    fps: int,
    seconds: float,
    crf: int,
    colors: Dict[str, str],
    fonts: Dict[str, str],
) -> None:
    score_line, delta_line = build_metric_lines(row)

    legend_items = [variant for variant in row.available_variants if variant in {"baseline", "ext2", "adaptmanip", "method"}]
    legend_start = 64
    legend_gap = 170
    legend_filters: List[str] = []
    for idx, variant in enumerate(legend_items):
        x = legend_start + idx * legend_gap
        color = ffmpeg_color(colors.get(variant, colors["ink_secondary"]))
        legend_filters.append(f"drawbox=x={x}:y={height - 52}:w=20:h=20:color={color}:t=fill")
        legend_filters.append(
            drawtext(
                fontfile=fonts["font_regular"],
                text=variant_label(variant),
                x=x + 28,
                y=height - 54,
                size=19,
                color=ffmpeg_color(colors["ink_secondary"]),
            )
        )

    vf_parts: List[str] = [
        f"fps={fps}",
        "scale=760:428:flags=lanczos",
        f"pad={width}:{height}:260:146:color={ffmpeg_color(colors['bg_panel'])}",
        f"drawbox=x=248:y=134:w=784:h=452:color={ffmpeg_color(colors['ink_primary'], 0.28)}:t=3",
        f"drawbox=x=0:y=0:w={width}:h=126:color={ffmpeg_color(colors['bg_panel'])}:t=fill",
        f"drawbox=x=0:y={height - 138}:w={width}:h=138:color={ffmpeg_color(colors['bg_panel'])}:t=fill",
        drawtext(
            fontfile=fonts["font_bold"],
            text=f"Scenario: {scenario_title(row.scenario)}",
            x=64,
            y=30,
            size=32,
            color=ffmpeg_color(colors["ink_primary"]),
        ),
        drawtext(
            fontfile=fonts["font_regular"],
            text=scenario_subtitle(row.scenario),
            x=64,
            y=70,
            size=21,
            color=ffmpeg_color(colors["ink_secondary"]),
        ),
        drawtext(
            fontfile=fonts["font_regular"],
            text="Bar height metric: mean success [0,1], higher is better.",
            x=64,
            y=98,
            size=19,
            color=ffmpeg_color(colors["ink_secondary"]),
        ),
        drawtext(
            fontfile=fonts["font_regular"],
            text="Bars rise to final values; this is not a time-series metric.",
            x=64,
            y=height - 78,
            size=17,
            color=ffmpeg_color(colors["ink_secondary"]),
        ),
    ]
    if score_line:
        vf_parts.append(
            drawtext(
                fontfile=fonts["font_regular"],
                text=score_line,
                x=600,
                y=height - 122,
                size=18,
                color=ffmpeg_color(colors["ink_primary"]),
            )
        )
    if delta_line:
        vf_parts.append(
            drawtext(
                fontfile=fonts["font_regular"],
                text=delta_line,
                x=600,
                y=height - 100,
                size=18,
                color=ffmpeg_color(colors["ink_primary"]),
            )
        )
    vf_parts.extend(legend_filters)

    run_ffmpeg(
        [
            "-y",
            "-stream_loop",
            "-1",
            "-i",
            rel(row.clip),
            "-t",
            f"{seconds:.2f}",
            "-vf",
            ",".join(vf_parts),
            "-r",
            str(fps),
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            str(crf),
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            rel(out_path),
        ]
    )


def concat_segments(parts: List[pathlib.Path], out_path: pathlib.Path, crf: int) -> None:
    list_path = ROOT / f"_corepaper_concat_{out_path.stem}.txt"
    lines = [f"file '{rel(p)}'" for p in parts]
    list_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    run_ffmpeg(
        [
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            rel(list_path),
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            str(crf),
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            rel(out_path),
        ]
    )
    list_path.unlink(missing_ok=True)


def row_from_manifest(row: Dict) -> ScenarioRow:
    clip = resolve_path(str(row.get("clip", "")))
    baseline_mean = row.get("baseline_mean")
    ext2_mean = row.get("ext2_mean")
    adaptmanip_mean = row.get("adaptmanip_mean")
    method_mean = row.get("method_mean")
    available = list(row.get("available_variants", []))
    if not available:
        if baseline_mean is not None:
            available.append("baseline")
        if ext2_mean is not None:
            available.append("ext2")
        if adaptmanip_mean is not None:
            available.append("adaptmanip")
        if method_mean is not None:
            available.append("method")

    return ScenarioRow(
        scenario=str(row.get("scenario")),
        available_variants=available,
        baseline_mean=float(baseline_mean) if baseline_mean is not None else None,
        ext2_mean=float(ext2_mean) if ext2_mean is not None else None,
        adaptmanip_mean=float(adaptmanip_mean) if adaptmanip_mean is not None else None,
        method_mean=float(method_mean) if method_mean is not None else None,
        delta=float(row.get("delta")) if row.get("delta") is not None else None,
        delta_vs_ext2=float(row.get("delta_vs_ext2")) if row.get("delta_vs_ext2") is not None else None,
        clip=clip,
    )


def main() -> int:
    args = parse_args()
    manifest_path = resolve_path(args.manifest)
    identity_path = resolve_path(args.identity)
    output_dir = resolve_path(args.output_dir)
    submission_dir = resolve_path(args.submission_dir)
    segments_dir = output_dir / "segments"
    pipeline_manifest_path = output_dir / "corepaper_video_pipeline_manifest.json"

    manifest = load_json(manifest_path)
    identity = load_json(identity_path)
    palette = identity.get("palette", {})
    colors: Dict[str, str] = {
        "ink_primary": str(palette.get("ink_primary", "#0F172A")),
        "ink_secondary": str(palette.get("ink_secondary", "#334155")),
        "bg_canvas": str(palette.get("bg_canvas", "#F4F7FB")),
        "bg_panel": str(palette.get("bg_panel", "#E6EDF7")),
        "baseline": str(palette.get("baseline", "#7A8896")),
        "ext2": str(palette.get("reference_b", "#F28E2B")),
        "adaptmanip": str(palette.get("reference_d", "#2CA58D")),
        "method": str(palette.get("method", "#D62728")),
    }
    fonts = identity.get("typography", {}).get("video", {})
    defaults = identity.get("video_defaults", {})

    width = int(defaults.get("width_px", 1280))
    height = int(defaults.get("height_px", 720))
    fps = int(defaults.get("fps", 30))
    intro_seconds = float(defaults.get("intro_seconds", 2.5))
    segment_seconds = float(defaults.get("segment_seconds", 4.0))
    outro_seconds = float(defaults.get("outro_seconds", 2.0))

    output_dir.mkdir(parents=True, exist_ok=True)
    submission_dir.mkdir(parents=True, exist_ok=True)
    segments_dir.mkdir(parents=True, exist_ok=True)

    for stale in segments_dir.glob("corepaper_segment_*.mp4"):
        stale.unlink(missing_ok=True)

    removed = remove_legacy_gifs(output_dir, submission_dir)
    if removed:
        print(f"Removed {removed} legacy GIF assets.")

    rows_map: Dict[str, ScenarioRow] = {}
    for item in manifest.get("comparisons", []):
        row = row_from_manifest(item)
        rows_map[row.scenario] = row

    requested = [s.strip() for s in args.scenario_order.split(",") if s.strip()]
    selected = [rows_map[s] for s in requested if s in rows_map and rows_map[s].clip.is_file()]
    if not selected:
        selected = [row for row in rows_map.values() if row.clip.is_file()][:5]
    if not selected:
        raise SystemExit("No valid scenario clips available to polish.")

    intro_path = segments_dir / "corepaper_segment_00_intro.mp4"
    create_intro_card(
        out_path=intro_path,
        width=width,
        height=height,
        fps=fps,
        seconds=intro_seconds,
        crf=args.crf,
        colors=colors,
        fonts=fonts,
    )

    segment_paths: List[pathlib.Path] = [intro_path]
    for idx, row in enumerate(selected, start=1):
        out_path = segments_dir / f"corepaper_segment_{idx:02d}_{row.scenario}.mp4"
        create_scenario_segment(
            row=row,
            out_path=out_path,
            width=width,
            height=height,
            fps=fps,
            seconds=segment_seconds,
            crf=args.crf,
            colors=colors,
            fonts=fonts,
        )
        segment_paths.append(out_path)

    outro_idx = len(segment_paths)
    outro_path = segments_dir / f"corepaper_segment_{outro_idx:02d}_outro.mp4"
    create_outro_card(
        out_path=outro_path,
        width=width,
        height=height,
        fps=fps,
        seconds=outro_seconds,
        crf=args.crf,
        colors=colors,
        fonts=fonts,
    )
    segment_paths.append(outro_path)

    polished_mp4 = output_dir / "corepaper_video_polished.mp4"
    submission_mp4 = submission_dir / "corepaper_video.mp4"

    concat_segments(segment_paths, polished_mp4, crf=args.crf)
    shutil.copy2(polished_mp4, submission_mp4)

    total_seconds = intro_seconds + (segment_seconds * len(selected)) + outro_seconds
    pipeline_manifest = {
        "identity_source": rel(identity_path),
        "base_manifest": rel(manifest_path),
        "video_spec": {
            "width_px": width,
            "height_px": height,
            "fps": fps,
            "intro_seconds": intro_seconds,
            "segment_seconds": segment_seconds,
            "outro_seconds": outro_seconds,
            "total_seconds": round(total_seconds, 2),
        },
        "scenarios": [
            {
                "scenario": row.scenario,
                "available_variants": row.available_variants,
                "baseline_mean": round(row.baseline_mean, 4) if row.baseline_mean is not None else None,
                "ext2_mean": round(row.ext2_mean, 4) if row.ext2_mean is not None else None,
                "adaptmanip_mean": round(row.adaptmanip_mean, 4) if row.adaptmanip_mean is not None else None,
                "method_mean": round(row.method_mean, 4) if row.method_mean is not None else None,
                "delta": round(row.delta, 4) if row.delta is not None else None,
                "delta_vs_ext2": round(row.delta_vs_ext2, 4) if row.delta_vs_ext2 is not None else None,
                "source_clip": rel(row.clip),
            }
            for row in selected
        ],
        "segments": [rel(p) for p in segment_paths],
        "outputs": {
            "polished_mp4": rel(polished_mp4),
            "submission_mp4": rel(submission_mp4),
        },
        "video_format": "mp4",
        "legacy_gifs_removed": removed,
    }
    pipeline_manifest_path.write_text(json.dumps(pipeline_manifest, indent=2) + "\n", encoding="utf-8")

    readme_path = output_dir / "README.md"
    lines: List[str] = []
    lines.append("# Video Assets")
    lines.append("")
    lines.append("- Base clips: generated with `scripts/vis/render_video.py`.")
    lines.append("- Polished cut: generated with `scripts/vis/polish_video.py`.")
    lines.append("- Full pipeline: `scripts/vis/build_video_pipeline.py`.")
    lines.append("- Output format: MP4 only.")
    lines.append("")
    lines.append("## Main Outputs")
    lines.append("")
    lines.append(f"- Base manifest: `{rel(manifest_path)}`")
    lines.append(f"- Pipeline manifest: `{rel(pipeline_manifest_path)}`")
    lines.append(f"- Polished MP4: `{rel(polished_mp4)}`")
    lines.append(f"- Submission MP4: `{rel(submission_mp4)}`")
    lines.append("")
    lines.append("## Scenario Segments")
    lines.append("")
    for row in selected:
        parts: List[str] = []
        if row.baseline_mean is not None:
            parts.append(f"Baseline={row.baseline_mean:.4f}")
        if row.ext2_mean is not None:
            parts.append(f"PPO-CVaR={row.ext2_mean:.4f}")
        if row.adaptmanip_mean is not None:
            parts.append(f"adaptmanip={row.adaptmanip_mean:.4f}")
        if row.method_mean is not None:
            parts.append(f"CORE={row.method_mean:.4f}")
        if row.delta is not None:
            parts.append(f"Delta(CORE-Baseline)={row.delta:+.4f}")
        if row.delta_vs_ext2 is not None:
            parts.append(f"Delta(CORE-PPO-CVaR)={row.delta_vs_ext2:+.4f}")
        lines.append(f"- `{row.scenario}`: " + ", ".join(parts))

    readme_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")

    print(f"Wrote polished video: {polished_mp4}")
    print(f"Wrote submission mp4: {submission_mp4}")
    print(f"Wrote pipeline manifest: {pipeline_manifest_path}")
    print(f"Wrote video README: {readme_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
