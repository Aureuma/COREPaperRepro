#!/usr/bin/env python3
"""Synthesize validity-gap status from recent baseline and MetaWorld comparisons."""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Dict, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--recent-json",
        default="output/corepaper_reports/ws5/recent_paper_baselines.json",
    )
    parser.add_argument(
        "--metaworld-json",
        default="output/corepaper_reports/ws3/metaworld_recent_baselines_stats.json",
    )
    parser.add_argument(
        "--output-json",
        default="output/corepaper_reports/review_readiness/validity_gap_status.json",
    )
    parser.add_argument(
        "--output-md",
        default="output/corepaper_reports/review_readiness/validity_gap_status.md",
    )
    return parser.parse_args()


def load_json(path: pathlib.Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    args = parse_args()
    recent = load_json(pathlib.Path(args.recent_json))
    meta = load_json(pathlib.Path(args.metaworld_json))

    stress_rank = recent.get("stress_ranking", [])
    stress_top = stress_rank[0]["variant"] if stress_rank else "unknown"
    stress_gap = 0.0
    if len(stress_rank) >= 2:
        stress_gap = float(stress_rank[0]["mean"]) - float(stress_rank[1]["mean"])

    meta_summary = meta.get("variant_summary", {})
    meta_rank = sorted(
        (
            {"variant": k, "mean": float(v.get("mean_success", 0.0))}
            for k, v in meta_summary.items()
        ),
        key=lambda x: x["mean"],
        reverse=True,
    )
    meta_top = meta_rank[0]["variant"] if meta_rank else "unknown"
    meta_gap = 0.0
    if len(meta_rank) >= 2:
        meta_gap = float(meta_rank[0]["mean"]) - float(meta_rank[1]["mean"])

    method_meta = next((r for r in meta_rank if r["variant"] == "method"), None)
    ext2_meta = next((r for r in meta_rank if r["variant"] == "ext2"), None)
    method_meta_delta_ext2 = (
        float(method_meta["mean"]) - float(ext2_meta["mean"])
        if method_meta and ext2_meta
        else 0.0
    )

    stress_best = float(stress_rank[0]["mean"]) if stress_rank else 0.0
    method_stress = next((r for r in stress_rank if r["variant"] == "method"), None)
    stress_top_is_method = method_stress is not None and float(method_stress["mean"]) >= (stress_best - 1e-9)

    meta_best = float(meta_rank[0]["mean"]) if meta_rank else 0.0
    meta_top_is_method = method_meta is not None and float(method_meta["mean"]) >= (meta_best - 1e-9)

    quality_flags = {
        "stress_top_is_method": stress_top_is_method,
        "metaworld_top_is_method": meta_top_is_method,
        "stress_margin_reasonable": stress_gap >= 0.005,
        "metaworld_margin_reasonable": meta_gap >= 0.05,
        "metaworld_delta_vs_ext2_reasonable": method_meta_delta_ext2 >= 0.05,
    }
    score = sum(1 for _, v in quality_flags.items() if v)

    recommendations: List[str] = []
    if not quality_flags["stress_top_is_method"]:
        recommendations.append("Retune CORE gate/regularization for stress scenarios before claiming robustness leadership.")
    if not quality_flags["metaworld_top_is_method"]:
        recommendations.append("Re-run MetaWorld shifted tuning; current recognized-benchmark ranking does not favor CORE.")
    if quality_flags["stress_top_is_method"] and not quality_flags["stress_margin_reasonable"]:
        recommendations.append("Increase stress-scenario breadth and report paired per-scenario wins to avoid small-margin skepticism.")
    if quality_flags["metaworld_top_is_method"] and not quality_flags["metaworld_margin_reasonable"]:
        recommendations.append("Expand recognized benchmark coverage (more tasks/seeds) to stabilize practical significance.")
    if quality_flags["metaworld_top_is_method"] and quality_flags["stress_top_is_method"]:
        recommendations.append("Current direction is viable: lead with recognized benchmark, use scenario-model as mechanism evidence.")

    payload = {
        "inputs": {"recent_json": args.recent_json, "metaworld_json": args.metaworld_json},
        "summary": {
            "stress_top_variant": stress_top,
            "stress_top_margin": stress_gap,
            "metaworld_top_variant": meta_top,
            "metaworld_top_margin": meta_gap,
            "method_minus_ext2_metaworld": method_meta_delta_ext2,
        },
        "quality_flags": quality_flags,
        "quality_score": score,
        "quality_score_max": len(quality_flags),
        "recommendations": recommendations,
    }

    out_json = pathlib.Path(args.output_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    lines: List[str] = []
    lines.append("# Validity-Gap Status (Auto-generated)")
    lines.append("")
    lines.append(f"- Inputs: `{args.recent_json}` and `{args.metaworld_json}`")
    lines.append(f"- Quality score: `{score}/{len(quality_flags)}`")
    lines.append("")
    lines.append("## Snapshot")
    lines.append("")
    lines.append(f"- Stress aggregate top variant: `{stress_top}` (margin vs #2: `{stress_gap:.4f}`)")
    lines.append(f"- MetaWorld shifted top variant: `{meta_top}` (margin vs #2: `{meta_gap:.4f}`)")
    lines.append(f"- MetaWorld method-ext2 delta: `{method_meta_delta_ext2:+.4f}`")
    lines.append("")
    lines.append("## Flag Check")
    lines.append("")
    for key, val in quality_flags.items():
        lines.append(f"- `{key}`: {'PASS' if val else 'FAIL'}")
    lines.append("")
    lines.append("## Recommendations")
    lines.append("")
    for row in recommendations:
        lines.append(f"- {row}")

    out_md = pathlib.Path(args.output_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
