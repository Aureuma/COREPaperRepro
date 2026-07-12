#!/usr/bin/env python3
"""Validate citation keys used by the IROS 2026 LaTeX package."""

from __future__ import annotations

import pathlib
import re
import sys
from typing import Dict, List, Set

ROOT = pathlib.Path(__file__).resolve().parents[2]
PAPER_DIR = ROOT / "paper"

BIB_KEY_RE = re.compile(r"@\w+\{([^,]+),")
CITE_RE = re.compile(
    r"\\cite[a-zA-Z*]*\s*(?:\[[^\]]*\])?\s*(?:\[[^\]]*\])?\s*\{([^}]*)\}"
)


def load_bib_keys(path: pathlib.Path) -> Set[str]:
    keys: Set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        m = BIB_KEY_RE.search(line)
        if m:
            keys.add(m.group(1).strip())
    return keys


def extract_citations(path: pathlib.Path) -> List[str]:
    content = path.read_text(encoding="utf-8")
    keys: List[str] = []
    for m in CITE_RE.finditer(content):
        raw = m.group(1)
        for token in raw.split(","):
            key = token.strip()
            if key:
                keys.append(key)
    return keys


def main() -> int:
    errors: List[str] = []

    if not PAPER_DIR.is_dir():
        print(f"Missing paper directory: {PAPER_DIR}", file=sys.stderr)
        return 1

    bib_files = sorted(PAPER_DIR.glob("*.bib"))
    if not bib_files:
        print(f"No bibliography files found under {PAPER_DIR}", file=sys.stderr)
        return 1

    bib_keys: Set[str] = set()
    for bib in bib_files:
        bib_keys.update(load_bib_keys(bib))
    if not bib_keys:
        print(f"No BibTeX entries found in {PAPER_DIR}", file=sys.stderr)
        return 1

    tex_files = sorted(PAPER_DIR.rglob("*.tex"))
    if not tex_files:
        print(f"No .tex files found under {PAPER_DIR}", file=sys.stderr)
        return 1

    used_keys: Set[str] = set()
    missing: Dict[pathlib.Path, List[str]] = {}

    for tex in tex_files:
        cited = extract_citations(tex)
        if not cited:
            continue
        bad = [k for k in cited if k not in bib_keys]
        if bad:
            missing[tex] = sorted(set(bad))
        used_keys.update(cited)

    if missing:
        for tex, bad_keys in missing.items():
            errors.append(f"Unknown citation key(s) in {tex}: {', '.join(bad_keys)}")

    if not used_keys:
        errors.append("No citations found in IROS .tex files.")

    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1

    uncited = len(bib_keys - used_keys)
    print(
        "IROS citation validation successful: "
        f"{len(used_keys)} cited keys, {len(bib_keys)} bib entries "
        f"from {len(bib_files)} .bib files, {uncited} uncited entries."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
