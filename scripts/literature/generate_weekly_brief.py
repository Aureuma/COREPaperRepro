#!/usr/bin/env python3
"""Generate weekly literature brief from delta and structured evidence artifacts."""

from __future__ import annotations

import argparse
import json
import pathlib
from datetime import datetime, timezone
from typing import Dict, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", required=True, help="Current metadata JSONL.")
    parser.add_argument("--structured-evidence", required=True, help="Structured evidence JSONL.")
    parser.add_argument("--delta", required=True, help="Weekly delta markdown.")
    parser.add_argument("--output", required=True, help="Weekly brief markdown output.")
    parser.add_argument("--max-papers", type=int, default=10, help="Max highlighted papers.")
    return parser.parse_args()


def load_jsonl(path: pathlib.Path) -> List[Dict]:
    rows: List[Dict] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def extract_new_ids_from_delta(path: pathlib.Path) -> List[str]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    new_ids: List[str] = []
    in_new_section = False
    for line in lines:
        if line.strip() == "## New Papers":
            in_new_section = True
            continue
        if line.startswith("## ") and line.strip() != "## New Papers":
            in_new_section = False
        if not in_new_section:
            continue
        if line.startswith("| `") and "` |" in line:
            aid = line.split("`", 2)[1].strip()
            if aid and aid != "_none_":
                new_ids.append(aid)
    return new_ids


def top_rows(rows: List[Dict], new_ids: List[str], limit: int) -> List[Dict]:
    by_id = {str(r.get("arxiv_id", "")): r for r in rows}
    selected: List[Dict] = []
    for aid in new_ids:
        if aid in by_id:
            selected.append(by_id[aid])
    if len(selected) < limit:
        remaining = sorted(rows, key=lambda x: x.get("updated", ""), reverse=True)
        for row in remaining:
            if row in selected:
                continue
            selected.append(row)
            if len(selected) >= limit:
                break
    return selected[:limit]


def safe(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ").strip()


def main() -> int:
    args = parse_args()
    metadata_rows = load_jsonl(pathlib.Path(args.metadata))
    evidence_rows = load_jsonl(pathlib.Path(args.structured_evidence))
    evidence_by_id = {str(row.get("arxiv_id", "")): row for row in evidence_rows}
    new_ids = extract_new_ids_from_delta(pathlib.Path(args.delta))

    merged_rows: List[Dict] = []
    for row in metadata_rows:
        aid = str(row.get("arxiv_id", ""))
        merged = dict(row)
        merged.update(evidence_by_id.get(aid, {}))
        merged_rows.append(merged)

    selected = top_rows(merged_rows, new_ids, args.max_papers)
    counts = {
        "core": sum(1 for r in merged_rows if r.get("relevance_tag") == "core"),
        "adjacent": sum(1 for r in merged_rows if r.get("relevance_tag") == "adjacent"),
        "background": sum(1 for r in merged_rows if r.get("relevance_tag") == "background"),
    }

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines: List[str] = []
    lines.append("# Weekly Literature Brief (Auto-generated)")
    lines.append("")
    lines.append(f"Week ending: `{now}`")
    lines.append("Owner: TBA")
    lines.append("")
    lines.append("## Snapshot Summary")
    lines.append("")
    lines.append(f"- Total tracked papers: {len(merged_rows)}")
    lines.append(f"- Newly discovered papers from delta: {len(new_ids)}")
    lines.append(f"- Tagged `core`: {counts['core']}")
    lines.append(f"- Tagged `adjacent`: {counts['adjacent']}")
    lines.append(f"- Tagged `background`: {counts['background']}")
    lines.append("- Potential novelty risks: review top `core` rows and update positioning memo.")
    lines.append("")
    lines.append("## Most Important Papers")
    lines.append("")
    lines.append("| Paper | Why It Matters | Required Action | Owner | Due |")
    lines.append("|---|---|---|---|---|")
    for row in selected:
        aid = safe(str(row.get("arxiv_id", "")))
        title = safe(str(row.get("title", "")))
        relevance = safe(str(row.get("relevance_tag", "")))
        method = safe(str(row.get("method_core", ""))[:180])
        why = f"{relevance}: {title}"
        action = "Tag as core/adjacent and map to claim-citation matrix."
        if method:
            action = "Extract method differences and compare against WS6 novelty memo."
        lines.append(f"| `{aid}` | {safe(why)} | {safe(action)} | TBA | +7d |")
    if not selected:
        lines.append("| _none_ |  |  |  |  |")
    lines.append("")
    lines.append("## Positioning Impact")
    lines.append("")
    lines.append("- Claims impacted in current draft: `C1-C5` pending explicit review.")
    lines.append("- Baselines that may need adding: inspect top `core` papers from this week.")
    lines.append("- Related-work sections needing update: Section 2 and novelty memo.")
    lines.append("")
    lines.append("## Open Questions")
    lines.append("")
    lines.append("- Q1: Which new papers are true methodological competitors?")
    lines.append("- Q2: Do any new papers invalidate current novelty framing?")
    lines.append("- Q3: Which additional baselines are mandatory for fairness?")

    output_path = pathlib.Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    print(f"Weekly brief written to: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

