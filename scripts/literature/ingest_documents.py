#!/usr/bin/env python3
"""Ingest downloaded paper files and extract useful text snippets."""

from __future__ import annotations

import argparse
import html
import json
import pathlib
import re
import shutil
import subprocess
from typing import Dict, Iterable, List, Optional, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", required=True, help="Directory containing raw downloaded papers.")
    parser.add_argument("--output-dir", required=True, help="Directory to store extracted text.")
    parser.add_argument("--records-out", required=True, help="JSONL output path for ingestion records.")
    return parser.parse_args()


def ensure_parent(path: pathlib.Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_jsonl(path: pathlib.Path, rows: Iterable[Dict]) -> None:
    ensure_parent(path)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def normalize_text(text: str) -> str:
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_html_text(path: pathlib.Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    raw = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", raw)
    raw = re.sub(r"(?is)<br\s*/?>", "\n", raw)
    raw = re.sub(r"(?is)</(p|div|section|article|h1|h2|h3|h4|li)>", "\n", raw)
    raw = re.sub(r"(?is)<[^>]+>", " ", raw)
    return normalize_text(html.unescape(raw))


def extract_pdf_text(path: pathlib.Path, output_txt: pathlib.Path) -> Tuple[str, str]:
    tool = shutil.which("pdftotext")
    if not tool:
        return "", "pdftotext_not_found"

    ensure_parent(output_txt)
    cmd = [tool, "-layout", str(path), str(output_txt)]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return "", f"pdftotext_failed:{result.returncode}"

    text = output_txt.read_text(encoding="utf-8", errors="ignore")
    return normalize_text(text), "ok"


def snippet(text: str, keyword: str, radius: int = 800) -> str:
    if not text:
        return ""
    lowered = text.lower()
    idx = lowered.find(keyword.lower())
    if idx == -1:
        return ""
    start = max(idx - radius // 3, 0)
    end = min(idx + radius, len(text))
    return text[start:end].strip()


def section_snippets(text: str) -> Dict[str, str]:
    return {
        "introduction": snippet(text, "introduction"),
        "method": snippet(text, "method"),
        "experiment": snippet(text, "experiment"),
        "result": snippet(text, "result"),
        "conclusion": snippet(text, "conclusion"),
    }


def safe_rel_path(root: pathlib.Path, source: pathlib.Path) -> str:
    rel = source.relative_to(root).as_posix()
    return rel.replace("/", "__")


def main() -> int:
    args = parse_args()
    input_dir = pathlib.Path(args.input_dir)
    output_dir = pathlib.Path(args.output_dir)
    records_out = pathlib.Path(args.records_out)
    text_dir = output_dir / "text"
    text_dir.mkdir(parents=True, exist_ok=True)

    records: List[Dict] = []
    files = sorted(
        list(input_dir.rglob("*.html")) + list(input_dir.rglob("*.pdf")),
        key=lambda p: p.as_posix(),
    )

    for source in files:
        ext = source.suffix.lower().lstrip(".")
        aid = source.parent.name
        text = ""
        status = "ok"

        txt_path: Optional[pathlib.Path] = text_dir / f"{safe_rel_path(input_dir, source)}.txt"
        if ext == "html":
            text = extract_html_text(source)
            if txt_path is not None:
                ensure_parent(txt_path)
                txt_path.write_text(text, encoding="utf-8")
        elif ext == "pdf":
            if txt_path is None:
                status = "output_path_error"
            else:
                text, status = extract_pdf_text(source, txt_path)
            if status != "ok":
                txt_path = None
        else:
            status = "unsupported_format"

        record = {
            "arxiv_id_hint": aid,
            "source_path": str(source),
            "format": ext,
            "extraction_status": status,
            "text_path": str(txt_path) if txt_path is not None else "",
            "char_count": len(text),
            "section_snippets": section_snippets(text),
        }
        records.append(record)

    write_jsonl(records_out, records)
    print(f"Ingested {len(records)} files.")
    print(f"Records written to: {records_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
