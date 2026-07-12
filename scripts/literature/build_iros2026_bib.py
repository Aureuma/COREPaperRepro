#!/usr/bin/env python3
"""Build BibTeX references and citation key map from curated metadata."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
from datetime import datetime, timezone
from typing import Dict, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-jsonl", required=True, help="Curated metadata JSONL path.")
    parser.add_argument("--output-bib", required=True, help="Output BibTeX file path.")
    parser.add_argument("--output-keymap", required=True, help="Output citation key map JSON path.")
    return parser.parse_args()


def load_jsonl(path: pathlib.Path) -> List[Dict]:
    rows: List[Dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def latex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "{": r"\{",
        "}": r"\}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "~": r"\~{}",
        "^": r"\^{}",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text


def year_from_iso(ts: str) -> str:
    return ts[:4] if ts and len(ts) >= 4 else "2026"


def make_key(arxiv_id: str) -> str:
    return "a" + re.sub(r"[^0-9a-zA-Z]+", "_", arxiv_id)


def to_bib_entry(row: Dict) -> str:
    arxiv_id = str(row.get("arxiv_id", "unknown"))
    key = make_key(arxiv_id)
    title = latex_escape(str(row.get("title", "")).strip())
    authors = [latex_escape(a.strip()) for a in row.get("authors", []) if a.strip()]
    author_field = " and ".join(authors) if authors else "Unknown"
    updated = str(row.get("updated", ""))
    year = year_from_iso(updated)
    abs_url = str(row.get("abs_url", f"https://arxiv.org/abs/{arxiv_id}"))
    category = ""
    cats = row.get("categories", [])
    if isinstance(cats, list) and cats:
        category = cats[0]

    lines = [
        f"@article{{{key},",
        f"  title        = {{{title}}},",
        f"  author       = {{{author_field}}},",
        f"  journal      = {{arXiv preprint arXiv:{arxiv_id}}},",
        f"  year         = {{{year}}},",
        f"  eprint       = {{{arxiv_id}}},",
        "  archivePrefix= {arXiv},",
        f"  primaryClass = {{{category}}},",
        f"  url          = {{{abs_url}}}",
        "}",
    ]
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    rows = load_jsonl(pathlib.Path(args.input_jsonl))
    rows.sort(key=lambda r: r.get("updated", ""), reverse=True)

    entries: List[str] = []
    keymap: Dict[str, Dict] = {}
    for row in rows:
        arxiv_id = str(row.get("arxiv_id", ""))
        key = make_key(arxiv_id)
        entries.append(to_bib_entry(row))
        keymap[key] = {
            "arxiv_id": arxiv_id,
            "title": row.get("title", ""),
            "category": row.get("iros2026_category", ""),
            "updated": row.get("updated", ""),
        }

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    header = "\n".join(
        [
            "% Auto-generated IROS 2026 literature bibliography",
            f"% Generated: {now}",
            f"% Entries: {len(entries)}",
            "",
        ]
    )
    bib_path = pathlib.Path(args.output_bib)
    bib_path.parent.mkdir(parents=True, exist_ok=True)
    bib_path.write_text(header + "\n\n".join(entries).strip() + "\n", encoding="utf-8")

    keymap_path = pathlib.Path(args.output_keymap)
    keymap_path.parent.mkdir(parents=True, exist_ok=True)
    keymap_path.write_text(json.dumps(keymap, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Wrote {bib_path} with {len(entries)} entries.")
    print(f"Wrote {keymap_path}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

