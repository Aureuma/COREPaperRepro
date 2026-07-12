#!/usr/bin/env python3
"""Build a shortlist of recent comparable papers and baseline mappings."""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Dict, List


CANDIDATES = [
    {
        "arxiv_id": "2602.14255v1",
        "baseline_variant": "latency_aware",
        "track": "implemented",
        "mapping_note": "Delay-aware control profile with reduced latency/dropout sensitivity and no rollback gate.",
    },
    {
        "arxiv_id": "2602.14363v1",
        "baseline_variant": "adaptmanip",
        "track": "implemented",
        "mapping_note": "Online recurrent state-estimation profile with stronger history adaptation and moderate robustness gains.",
    },
    {
        "arxiv_id": "2602.12616v1",
        "baseline_variant": "robust_cp",
        "track": "implemented",
        "mapping_note": "Conformal-style conservative safety profile emphasizing bounded worst-case degradation.",
    },
    {
        "arxiv_id": "2602.12047v1",
        "baseline_variant": "robust_cp",
        "track": "implemented_support",
        "mapping_note": "OOD-robust conformal control signal used as supporting reference for robust_cp behavior.",
    },
    {
        "arxiv_id": "2602.15010v1",
        "baseline_variant": "history_keyframe",
        "track": "implemented",
        "mapping_note": "History-keyframe policy profile with dropout-focused resilience and longer action delay to mimic keyframe-conditioned updates.",
    },
    {
        "arxiv_id": "2602.15567v1",
        "baseline_variant": "constrained_flow",
        "track": "implemented",
        "mapping_note": "Constraint-aware flow profile with stronger contact/jam tolerance and moderate latency robustness in the unified harness.",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", default="data/papers/metadata/arxiv_latest.jsonl")
    parser.add_argument("--output-json", default="output/corepaper_reports/literature/recent_baseline_candidates.json")
    parser.add_argument("--output-md", default="output/corepaper_reports/literature/recent_baseline_candidates.md")
    return parser.parse_args()


def load_metadata(path: pathlib.Path) -> Dict[str, Dict]:
    rows: Dict[str, Dict] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        rows[str(row.get("arxiv_id", ""))] = row
    return rows


def main() -> int:
    args = parse_args()
    meta = load_metadata(pathlib.Path(args.metadata))

    selected: List[Dict] = []
    for item in CANDIDATES:
        aid = item["arxiv_id"]
        row = meta.get(aid)
        if not row:
            continue
        selected.append(
            {
                "arxiv_id": aid,
                "title": row.get("title", ""),
                "published": row.get("published", ""),
                "updated": row.get("updated", ""),
                "abs_url": row.get("abs_url", f"https://arxiv.org/abs/{aid}"),
                "pdf_url": row.get("pdf_url", f"https://arxiv.org/pdf/{aid}.pdf"),
                "baseline_variant": item["baseline_variant"],
                "track": item["track"],
                "mapping_note": item["mapping_note"],
                "summary": row.get("summary", ""),
            }
        )

    payload = {
        "source_metadata": args.metadata,
        "selected_count": len(selected),
        "selected": selected,
    }
    out_json = pathlib.Path(args.output_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    lines: List[str] = []
    lines.append("# Recent Comparable Papers -> Baseline Mapping")
    lines.append("")
    lines.append(f"- Source metadata: `{args.metadata}`")
    lines.append(f"- Selected papers: `{len(selected)}`")
    lines.append("")
    lines.append("| arXiv ID | Published | Baseline Variant | Track | Why Applicable |")
    lines.append("|---|---|---|---|---|")
    for row in selected:
        lines.append(
            f"| [{row['arxiv_id']}]({row['abs_url']}) | {row['published'][:10]} | "
            f"`{row['baseline_variant']}` | {row['track']} | {row['mapping_note']} |"
        )

    lines.append("")
    lines.append("## Shortlist Notes")
    lines.append("")
    for row in selected:
        lines.append(f"### {row['arxiv_id']} - {row['title']}")
        lines.append(f"- URL: {row['abs_url']}")
        lines.append(f"- Mapping: `{row['baseline_variant']}` ({row['track']})")
        lines.append(f"- Note: {row['mapping_note']}")
        lines.append("")

    out_md = pathlib.Path(args.output_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
