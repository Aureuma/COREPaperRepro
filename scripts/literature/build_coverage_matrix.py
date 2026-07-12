#!/usr/bin/env python3
"""Build a markdown coverage matrix from metadata snapshots."""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Dict, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", required=True, help="Input metadata JSONL file.")
    parser.add_argument("--output", required=True, help="Output markdown file.")
    parser.add_argument("--limit", type=int, default=150, help="Maximum rows to include.")
    return parser.parse_args()


def load_jsonl(path: pathlib.Path) -> List[Dict]:
    rows: List[Dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def escape_md_cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ").strip()


def main() -> int:
    args = parse_args()
    metadata_path = pathlib.Path(args.metadata)
    output_path = pathlib.Path(args.output)

    rows = load_jsonl(metadata_path)
    rows = sorted(rows, key=lambda x: x.get("updated", ""), reverse=True)[: args.limit]

    lines: List[str] = []
    lines.append("# Coverage Matrix (Auto-generated)")
    lines.append("")
    lines.append(f"- Source: `{metadata_path}`")
    lines.append(f"- Total rows: {len(rows)}")
    lines.append("")
    lines.append("| arXiv ID | Updated | Query Buckets | Title | Relevance Tag | Review Status | Notes |")
    lines.append("|---|---|---|---|---|---|---|")

    if not rows:
        lines.append("| _none_ |  |  |  |  |  |  |")
    else:
        for row in rows:
            aid = escape_md_cell(row.get("arxiv_id", ""))
            updated = escape_md_cell(row.get("updated", ""))
            queries = escape_md_cell(", ".join(row.get("query_names", [])))
            title = escape_md_cell(row.get("title", ""))
            lines.append(f"| `{aid}` | {updated} | {queries} | {title} |  | pending |  |")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    print(f"Coverage matrix written to: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

