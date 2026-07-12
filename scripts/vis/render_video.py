#!/usr/bin/env python3
"""Generate lightweight MP4 rollout and comparison assets from experiment logs."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from typing import Dict, List, Tuple


ROOT = pathlib.Path(__file__).resolve().parents[2]
FFMPEG_DOCKER_IMAGE = "lscr.io/linuxserver/ffmpeg:latest"

EXTERNAL_PATTERN = re.compile(r"^(baseline|ext1|ext2|method)-s(\d+)$")
SOFT_PATTERN = re.compile(r"^(S\d+)-([a-z]+)-(baseline|method|ext2)-s\d+$")
SIM2SIM_PATTERN = re.compile(r"^SIM-([a-z0-9_]+)-(baseline|method|ext2)-s\d+$")


@dataclass
class RunScore:
    run_id: str
    score: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--external-logs", default="output/corepaper_logs/experiments/external_latest")
    parser.add_argument("--software-transfer-logs", default="output/corepaper_logs/experiments/software_transfer_latest")
    parser.add_argument("--sim2sim-logs", default="output/corepaper_logs/experiments/sim2sim_latest")
    parser.add_argument("--metaworld-stats", default="output/corepaper_reports/ws3/metaworld_recent_baselines_stats.json")
    parser.add_argument("--identity", default="config/visual_identity.json")
    parser.add_argument("--output-dir", default="output/corepaper_assets/video")
    parser.add_argument("--submission-dir", default="output/corepaper_submission")
    parser.add_argument("--frames", type=int, default=24)
    parser.add_argument("--fps", type=int, default=12)
    parser.add_argument("--crf", type=int, default=22)
    return parser.parse_args()


def load_json(path: pathlib.Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def collect_scores(log_dir: pathlib.Path) -> Dict[str, float]:
    scores: Dict[str, float] = {}
    for path in sorted(log_dir.glob("*.json")):
        if path.name == "suite_summary.json":
            continue
        payload = load_json(path)
        run_id = str(payload.get("run_id", ""))
        score = payload.get("metric_payload", {}).get("primary_metric")
        if run_id and score is not None:
            scores[run_id] = float(score)
    return scores


def mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def clamp01(v: float) -> float:
    return max(0.0, min(1.0, v))


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    raw = hex_color.strip().lstrip("#")
    if len(raw) != 6:
        return (127, 127, 127)
    return (int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16))


def rel(path: pathlib.Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


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


def write_ppm(path: pathlib.Path, width: int, height: int, pixels: bytearray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as f:
        header = f"P6\n{width} {height}\n255\n".encode("ascii")
        f.write(header)
        f.write(pixels)


def blank_canvas(width: int, height: int, rgb: Tuple[int, int, int]) -> bytearray:
    r, g, b = rgb
    row = bytes([r, g, b]) * width
    return bytearray(row * height)


def draw_rect(
    canvas: bytearray,
    width: int,
    height: int,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    rgb: Tuple[int, int, int],
) -> None:
    r, g, b = rgb
    x0 = max(0, min(width - 1, x0))
    x1 = max(0, min(width, x1))
    y0 = max(0, min(height - 1, y0))
    y1 = max(0, min(height, y1))
    if x1 <= x0 or y1 <= y0:
        return
    for y in range(y0, y1):
        base = y * width * 3
        for x in range(x0, x1):
            idx = base + x * 3
            canvas[idx] = r
            canvas[idx + 1] = g
            canvas[idx + 2] = b


def render_single_frame(
    width: int,
    height: int,
    score: float,
    progress: float,
    bar_color: Tuple[int, int, int],
) -> bytearray:
    canvas = blank_canvas(width, height, (248, 250, 252))
    draw_rect(canvas, width, height, 24, 20, width - 24, height - 20, (220, 226, 232))
    bar_bottom = height - 36
    bar_top = 40
    bar_left = width // 2 - 44
    bar_right = width // 2 + 44
    full_h = bar_bottom - bar_top
    target_h = int(full_h * clamp01(score))
    current_h = int(target_h * clamp01(progress))
    draw_rect(canvas, width, height, bar_left, bar_bottom - current_h, bar_right, bar_bottom, bar_color)
    return canvas


def render_comparison_frame(
    width: int,
    height: int,
    series: List[Tuple[float, Tuple[int, int, int]]],
    progress: float,
) -> bytearray:
    canvas = blank_canvas(width, height, (248, 250, 252))
    draw_rect(canvas, width, height, 16, 16, width - 16, height - 16, (220, 226, 232))

    bar_bottom = height - 34
    bar_top = 36
    full_h = bar_bottom - bar_top

    n = max(1, len(series))
    margin = 28
    avail = width - 2 * margin
    bar_w = min(64, max(34, int(avail / (2 * n))))
    gap = int((avail - (n * bar_w)) / (n + 1))

    for idx, (score, color) in enumerate(series):
        x0 = margin + gap * (idx + 1) + bar_w * idx
        x1 = x0 + bar_w
        target_h = int(full_h * clamp01(score))
        cur_h = int(target_h * clamp01(progress))
        draw_rect(canvas, width, height, x0, bar_bottom - cur_h, x1, bar_bottom, color)

    return canvas


def make_mp4(frame_pattern: pathlib.Path, output_path: pathlib.Path, fps: int, crf: int) -> bool:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    run_ffmpeg(
        [
            "-y",
            "-framerate",
            str(fps),
            "-i",
            rel(frame_pattern),
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
            rel(output_path),
        ]
    )
    return output_path.is_file() and output_path.stat().st_size > 0


def concat_mp4(parts: List[pathlib.Path], output_path: pathlib.Path, crf: int) -> bool:
    if not parts:
        return False
    output_path.parent.mkdir(parents=True, exist_ok=True)
    list_file = ROOT / f"_corepaper_concat_{output_path.stem}.txt"
    lines = [f"file '{rel(p)}'" for p in parts]
    list_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    run_ffmpeg(
        [
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            rel(list_file),
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
            rel(output_path),
        ]
    )
    list_file.unlink(missing_ok=True)
    return output_path.is_file() and output_path.stat().st_size > 0


def pick_best_worst_median(scores: List[RunScore]) -> Dict[str, RunScore]:
    ordered = sorted(scores, key=lambda row: row.score)
    if not ordered:
        return {}
    return {
        "worst": ordered[0],
        "median": ordered[len(ordered) // 2],
        "best": ordered[-1],
    }


def remove_legacy_gifs(*roots: pathlib.Path) -> int:
    removed = 0
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*.gif"):
            path.unlink(missing_ok=True)
            removed += 1
    return removed


def variant_display(variant: str) -> str:
    mapping = {
        "baseline": "Baseline",
        "ext1": "TRPO-U",
        "ext2": "PPO-CVaR",
        "adaptmanip": "adaptmanip",
        "method": "CORE",
    }
    return mapping.get(variant, variant)


def main() -> int:
    args = parse_args()
    output_dir = pathlib.Path(args.output_dir)
    submission_dir = pathlib.Path(args.submission_dir)
    rollouts_dir = output_dir / "rollouts"
    comparisons_dir = output_dir / "comparisons"
    manifest_path = output_dir / "manifest.json"

    output_dir.mkdir(parents=True, exist_ok=True)
    submission_dir.mkdir(parents=True, exist_ok=True)

    removed = remove_legacy_gifs(output_dir, submission_dir)
    if removed:
        print(f"Removed {removed} legacy GIF assets.")

    identity = load_json(pathlib.Path(args.identity))
    palette = identity.get("palette", {})
    colors = {
        "baseline": hex_to_rgb(str(palette.get("baseline", "#7A8896"))),
        "ext1": hex_to_rgb(str(palette.get("reference_a", "#59A14F"))),
        "ext2": hex_to_rgb(str(palette.get("reference_b", "#F28E2B"))),
        "adaptmanip": hex_to_rgb(str(palette.get("reference_d", "#2CA58D"))),
        "method": hex_to_rgb(str(palette.get("method", "#D62728"))),
    }

    external_scores = collect_scores(pathlib.Path(args.external_logs))
    soft_scores = collect_scores(pathlib.Path(args.software_transfer_logs))
    sim2sim_scores = collect_scores(pathlib.Path(args.sim2sim_logs))

    grouped_external: Dict[str, List[RunScore]] = {}
    for run_id, score in external_scores.items():
        match = EXTERNAL_PATTERN.match(run_id)
        if not match:
            continue
        group = match.group(1)
        grouped_external.setdefault(group, []).append(RunScore(run_id=run_id, score=score))

    selected_rollouts: List[Dict] = []
    clip_outputs: List[str] = []

    with tempfile.TemporaryDirectory(prefix="corepaper-video-", dir=output_dir) as tmp:
        tmp_path = pathlib.Path(tmp)
        width, height = 320, 180

        for group in ("baseline", "ext2", "method"):
            choices = pick_best_worst_median(grouped_external.get(group, []))
            for rank in ("best", "median", "worst"):
                row = choices.get(rank)
                if row is None:
                    continue
                frame_prefix = tmp_path / f"{group}_{rank}_%03d.ppm"
                for idx in range(args.frames):
                    progress = (idx + 1) / args.frames
                    frame = render_single_frame(width, height, row.score, progress, colors[group])
                    frame_file = tmp_path / f"{group}_{rank}_{idx:03d}.ppm"
                    write_ppm(frame_file, width, height, frame)
                out_file = rollouts_dir / f"{group}_{rank}.mp4"
                if make_mp4(frame_prefix, out_file, args.fps, args.crf):
                    clip_outputs.append(str(out_file))
                selected_rollouts.append(
                    {
                        "variant": group,
                        "label": variant_display(group),
                        "rank": rank,
                        "run_id": row.run_id,
                        "score": round(row.score, 4),
                        "clip": str(out_file),
                    }
                )

        scenario_metrics: Dict[str, Dict[str, float]] = {}

        soft_grouped: Dict[Tuple[str, str, str], List[float]] = {}
        for run_id, score in soft_scores.items():
            match = SOFT_PATTERN.match(run_id)
            if not match:
                continue
            test, severity, variant = match.groups()
            soft_grouped.setdefault((test, severity, variant), []).append(score)

        for test, severity in (("S1", "hard"), ("S2", "med"), ("S3", "severe")):
            base = mean(soft_grouped.get((test, severity, "baseline"), []))
            core = mean(soft_grouped.get((test, severity, "method"), []))
            if base > 0.0 or core > 0.0:
                scenario_metrics[f"{test}-{severity}"] = {"baseline": base, "method": core}

        sim_grouped: Dict[Tuple[str, str], List[float]] = {}
        for run_id, score in sim2sim_scores.items():
            match = SIM2SIM_PATTERN.match(run_id)
            if not match:
                continue
            engine, variant = match.groups()
            sim_grouped.setdefault((engine, variant), []).append(score)
        for engine in ("mujoco", "isaac"):
            means = {
                "baseline": mean(sim_grouped.get((engine, "baseline"), [])),
                "ext2": mean(sim_grouped.get((engine, "ext2"), [])),
                "method": mean(sim_grouped.get((engine, "method"), [])),
            }
            if any(v > 0.0 for v in means.values()):
                scenario_metrics[f"SIM-{engine}"] = means

        metaworld_stats_path = pathlib.Path(args.metaworld_stats)
        if metaworld_stats_path.is_file():
            mw = load_json(metaworld_stats_path)
            vs = mw.get("variant_summary", {})
            mw_means: Dict[str, float] = {}
            for variant in ("baseline", "ext2", "adaptmanip", "method"):
                val = vs.get(variant, {}).get("mean_success")
                if val is not None:
                    mw_means[variant] = float(val)
            if mw_means:
                scenario_metrics["META-shifted"] = mw_means

        scenario_priority = ["META-shifted", "S1-hard", "S2-med", "S3-severe", "SIM-isaac", "SIM-mujoco"]
        scenario_order = [s for s in scenario_priority if s in scenario_metrics] + [
            s for s in sorted(scenario_metrics.keys()) if s not in scenario_priority
        ]

        comparison_rows: List[Dict] = []
        for scenario in scenario_order:
            means = scenario_metrics[scenario]
            variants = [v for v in ("baseline", "ext2", "adaptmanip", "method") if v in means]
            series = [(means[v], colors[v]) for v in variants]
            if not series:
                continue

            frame_prefix = tmp_path / f"cmp_{scenario}_%03d.ppm"
            for idx in range(args.frames):
                progress = (idx + 1) / args.frames
                frame = render_comparison_frame(width, height, series, progress)
                frame_file = tmp_path / f"cmp_{scenario}_{idx:03d}.ppm"
                write_ppm(frame_file, width, height, frame)

            out_file = comparisons_dir / f"{scenario}.mp4"
            if make_mp4(frame_prefix, out_file, args.fps, args.crf):
                clip_outputs.append(str(out_file))

            baseline_mean = means.get("baseline")
            method_mean = means.get("method")
            ext2_mean = means.get("ext2")
            comparison_rows.append(
                {
                    "scenario": scenario,
                    "available_variants": variants,
                    "baseline_mean": round(baseline_mean, 4) if baseline_mean is not None else None,
                    "ext2_mean": round(ext2_mean, 4) if ext2_mean is not None else None,
                    "adaptmanip_mean": round(means.get("adaptmanip"), 4) if means.get("adaptmanip") is not None else None,
                    "method_mean": round(method_mean, 4) if method_mean is not None else None,
                    "delta": round(method_mean - baseline_mean, 4)
                    if method_mean is not None and baseline_mean is not None
                    else None,
                    "delta_vs_ext2": round(method_mean - ext2_mean, 4)
                    if method_mean is not None and ext2_mean is not None
                    else None,
                    "clip": str(out_file),
                }
            )

        rough_cut = submission_dir / "corepaper_video_rough_cut.mp4"
        selected_for_cut: List[pathlib.Path] = []
        for scenario in ("META-shifted", "S1-hard", "S2-med", "S3-severe", "SIM-isaac"):
            p = comparisons_dir / f"{scenario}.mp4"
            if p.is_file():
                selected_for_cut.append(p)
        if selected_for_cut:
            concat_mp4(selected_for_cut, rough_cut, args.crf)

        manifest = {
            "rollouts": selected_rollouts,
            "comparisons": comparison_rows,
            "rough_cut_mp4": str(rough_cut),
            "clips_generated": len([p for p in clip_outputs if pathlib.Path(p).is_file()]),
            "video_format": "mp4",
        }
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    readme_lines: List[str] = []
    readme_lines.append("# Video Assets")
    readme_lines.append("")
    readme_lines.append("- Auto-generated with `scripts/vis/render_video.py`.")
    readme_lines.append("- MP4 outputs only (GIF outputs removed).")
    readme_lines.append(f"- Rollout clips: `{rollouts_dir}`")
    readme_lines.append(f"- Side-by-side comparison clips: `{comparisons_dir}`")
    readme_lines.append(f"- Manifest: `{manifest_path}`")
    readme_lines.append(f"- Rough cut (MP4): `{submission_dir / 'corepaper_video_rough_cut.mp4'}`")
    readme_lines.append("")
    readme_lines.append("## Comparison Scenarios")
    readme_lines.append("")
    manifest = load_json(manifest_path)
    for row in manifest.get("comparisons", []):
        core = row.get("method_mean")
        base = row.get("baseline_mean")
        ext2 = row.get("ext2_mean")
        parts = []
        if base is not None:
            parts.append(f"Baseline={base:.4f}")
        if ext2 is not None:
            parts.append(f"PPO-CVaR={ext2:.4f}")
        if core is not None:
            parts.append(f"CORE={core:.4f}")
        delta = row.get("delta")
        if delta is not None:
            parts.append(f"Delta(CORE-Baseline)={delta:+.4f}")
        readme_lines.append(f"- `{row['scenario']}`: " + ", ".join(parts))
    (output_dir / "README.md").write_text("\n".join(readme_lines).strip() + "\n", encoding="utf-8")

    print(f"Wrote video assets to {output_dir}")
    print(f"Wrote manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
