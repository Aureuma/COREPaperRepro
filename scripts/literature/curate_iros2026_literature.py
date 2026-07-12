#!/usr/bin/env python3
"""Curate an IROS-2026-focused literature shortlist from raw metadata."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Tuple


INCLUDE_KEYWORDS: List[Tuple[str, int]] = [
    ("contact-rich", 6),
    ("contact rich", 6),
    ("manipulation", 5),
    ("robot learning", 4),
    ("imitation learning", 4),
    ("policy", 3),
    ("safe", 3),
    ("robust", 3),
    ("conformal", 3),
    ("domain shift", 3),
    ("sim2real", 3),
    ("tactile", 3),
    ("vision-language-action", 3),
    ("cross-embodiment", 3),
    ("world model", 2),
    ("long-horizon", 2),
    ("trajectory planning", 2),
    ("mpc", 2),
]

EXCLUDE_KEYWORDS: List[Tuple[str, int]] = [
    ("aircraft", -6),
    ("aam", -6),
    ("swarm", -4),
    ("endoluminal", -4),
    ("hanoi", -2),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Raw metadata JSONL path.")
    parser.add_argument("--output-jsonl", required=True, help="Curated metadata JSONL path.")
    parser.add_argument("--output-md", required=True, help="Curated markdown report path.")
    parser.add_argument("--limit", type=int, default=45, help="Max curated papers.")
    return parser.parse_args()


def load_jsonl(path: pathlib.Path) -> List[Dict]:
    rows: List[Dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def write_jsonl(path: pathlib.Path, rows: Iterable[Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def score_row(row: Dict) -> Tuple[int, List[str], List[str]]:
    text = normalize(f"{row.get('title','')} {row.get('summary','')}")
    score = 0
    matched_pos: List[str] = []
    matched_neg: List[str] = []
    for kw, weight in INCLUDE_KEYWORDS:
        if kw in text:
            score += weight
            matched_pos.append(kw)
    for kw, weight in EXCLUDE_KEYWORDS:
        if kw in text:
            score += weight
            matched_neg.append(kw)

    # Bias toward likely robotics-manipulation relevance.
    cats = set(row.get("categories", []))
    if "cs.RO" in cats:
        score += 2

    return score, matched_pos, matched_neg


def category_for(row: Dict) -> str:
    t = normalize(f"{row.get('title','')} {row.get('summary','')}")
    if any(k in t for k in ["safe", "robust", "conformal", "domain shift", "sim2real"]):
        return "robust-safe-control"
    if any(k in t for k in ["contact-rich", "manipulation", "tactile", "grasp"]):
        return "contact-rich-manipulation"
    if any(k in t for k in ["imitation", "policy", "history conditioning"]):
        return "imitation-policy-learning"
    if any(k in t for k in ["vision-language-action", "vla", "world model", "embodied"]):
        return "vla-world-models"
    return "adjacent"


def escape_md(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ").strip()


def main() -> int:
    args = parse_args()
    rows = load_jsonl(pathlib.Path(args.input))

    scored: List[Dict] = []
    for row in rows:
        score, matched_pos, matched_neg = score_row(row)
        row = dict(row)
        row["relevance_score"] = score
        row["matched_positive"] = matched_pos
        row["matched_negative"] = matched_neg
        row["iros2026_category"] = category_for(row)
        scored.append(row)

    scored.sort(key=lambda r: (r.get("relevance_score", 0), r.get("updated", "")), reverse=True)
    curated = [r for r in scored if r.get("relevance_score", 0) >= 5][: args.limit]

    # Ensure diversity: include at least one item per category if available.
    by_cat: Dict[str, List[Dict]] = {}
    for row in scored:
        by_cat.setdefault(row["iros2026_category"], []).append(row)
    for cat, items in by_cat.items():
        if not any(r["iros2026_category"] == cat for r in curated) and items:
            curated.append(items[0])
    # Re-sort and trim.
    seen = set()
    unique = []
    for row in sorted(curated, key=lambda r: (r.get("relevance_score", 0), r.get("updated", "")), reverse=True):
        aid = row.get("arxiv_id")
        if aid in seen:
            continue
        seen.add(aid)
        unique.append(row)
    curated = unique[: args.limit]

    write_jsonl(pathlib.Path(args.output_jsonl), curated)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    md_lines: List[str] = []
    md_lines.append("# IROS 2026 Curated Literature Shortlist")
    md_lines.append("")
    md_lines.append(f"- Generated: `{now}`")
    md_lines.append(f"- Source rows: {len(rows)}")
    md_lines.append(f"- Curated rows: {len(curated)}")
    md_lines.append("")
    md_lines.append("| arXiv ID | Updated | Category | Score | Title |")
    md_lines.append("|---|---|---|---:|---|")
    for row in curated:
        md_lines.append(
            f"| `{escape_md(row.get('arxiv_id',''))}` | {escape_md(row.get('updated',''))} | "
            f"{escape_md(row.get('iros2026_category',''))} | {int(row.get('relevance_score',0))} | "
            f"{escape_md(row.get('title',''))} |"
        )

    md_path = pathlib.Path(args.output_md)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text("\n".join(md_lines).strip() + "\n", encoding="utf-8")
    print(f"Curated {len(curated)} papers.")
    print(f"Wrote {args.output_jsonl}")
    print(f"Wrote {args.output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

