#!/usr/bin/env python3
"""Generate weekly literature delta from metadata snapshots."""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Dict, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current", required=True, help="Current metadata snapshot (JSONL).")
    parser.add_argument("--previous", help="Previous metadata snapshot (JSONL).")
    parser.add_argument("--output", required=True, help="Output markdown report path.")
    parser.add_argument("--max-items", type=int, default=40, help="Max rows per section.")
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


def index_by_id(rows: List[Dict]) -> Dict[str, Dict]:
    out: Dict[str, Dict] = {}
    for row in rows:
        aid = row.get("arxiv_id", "")
        if aid:
            out[aid] = row
    return out


def fmt_queries(row: Dict) -> str:
    names = row.get("query_names", [])
    if isinstance(names, list) and names:
        return ", ".join(names)
    return ""


def line_for_paper(row: Dict) -> str:
    title = (row.get("title", "") or "").replace("\n", " ").strip()
    aid = row.get("arxiv_id", "")
    updated = row.get("updated", "")
    queries = fmt_queries(row)
    return f"| `{aid}` | {updated} | {queries} | {title} |"


def main() -> int:
    args = parse_args()
    current_path = pathlib.Path(args.current)
    previous_path = pathlib.Path(args.previous) if args.previous else None
    output_path = pathlib.Path(args.output)

    current_rows = load_jsonl(current_path)
    previous_rows = load_jsonl(previous_path) if previous_path else []

    current = index_by_id(current_rows)
    previous = index_by_id(previous_rows)

    current_ids = set(current)
    previous_ids = set(previous)

    new_ids = sorted(current_ids - previous_ids)
    removed_ids = sorted(previous_ids - current_ids)
    updated_ids = sorted(
        aid
        for aid in (current_ids & previous_ids)
        if current[aid].get("updated", "") != previous[aid].get("updated", "")
    )

    lines: List[str] = []
    lines.append("# Weekly Literature Delta Report")
    lines.append("")
    lines.append(f"- Current snapshot: `{current_path}`")
    lines.append(f"- Previous snapshot: `{previous_path}`" if previous_path else "- Previous snapshot: `None`")
    lines.append(f"- Total current papers: {len(current_rows)}")
    lines.append(f"- New papers: {len(new_ids)}")
    lines.append(f"- Updated papers: {len(updated_ids)}")
    lines.append(f"- Removed papers: {len(removed_ids)}")
    lines.append("")

    lines.append("## New Papers")
    lines.append("")
    lines.append("| arXiv ID | Updated | Query Buckets | Title |")
    lines.append("|---|---|---|---|")
    for aid in new_ids[: args.max_items]:
        lines.append(line_for_paper(current[aid]))
    if not new_ids:
        lines.append("| _none_ |  |  |  |")
    lines.append("")

    lines.append("## Updated Papers")
    lines.append("")
    lines.append("| arXiv ID | Updated | Query Buckets | Title |")
    lines.append("|---|---|---|---|")
    for aid in updated_ids[: args.max_items]:
        lines.append(line_for_paper(current[aid]))
    if not updated_ids:
        lines.append("| _none_ |  |  |  |")
    lines.append("")

    lines.append("## Removed Papers")
    lines.append("")
    lines.append("| arXiv ID | Last Known Updated | Query Buckets | Title |")
    lines.append("|---|---|---|---|")
    for aid in removed_ids[: args.max_items]:
        lines.append(line_for_paper(previous[aid]))
    if not removed_ids:
        lines.append("| _none_ |  |  |  |")
    lines.append("")

    lines.append("## Reviewer-Risk Checks")
    lines.append("")
    lines.append("- [ ] Check whether any new papers alter novelty positioning.")
    lines.append("- [ ] Check whether any new baselines must be added to experiments.")
    lines.append("- [ ] Update related-work and claim-citation matrix accordingly.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    print(f"Weekly delta report written to: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

