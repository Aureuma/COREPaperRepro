#!/usr/bin/env python3
"""Generate a minimal valid PDF from plaintext/markdown without external dependencies."""

from __future__ import annotations

import argparse
import pathlib
import textwrap
from typing import Dict, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Input markdown/text file.")
    parser.add_argument("--output", required=True, help="Output PDF path.")
    parser.add_argument("--title", default="CORE Paper Draft")
    return parser.parse_args()


def escape_pdf_text(s: str) -> str:
    return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def paginate(lines: List[str], lines_per_page: int = 48) -> List[List[str]]:
    pages: List[List[str]] = []
    for i in range(0, len(lines), lines_per_page):
        pages.append(lines[i : i + lines_per_page])
    return pages if pages else [["(empty document)"]]


def build_pdf(pages: List[List[str]]) -> bytes:
    # Object IDs:
    # 1 catalog, 2 pages, 3 font, then content/page pairs.
    objects: Dict[int, bytes] = {}
    objects[1] = b"<< /Type /Catalog /Pages 2 0 R >>"
    objects[3] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"

    next_id = 4
    page_ids: List[int] = []
    for page_lines in pages:
        content_lines = ["BT /F1 10 Tf 12 TL 50 770 Td"]
        for line in page_lines:
            safe = escape_pdf_text(line)
            content_lines.append(f"({safe}) Tj T*")
        content_lines.append("ET")
        stream = "\n".join(content_lines).encode("latin-1", errors="replace")
        content_obj = (
            f"<< /Length {len(stream)} >>\nstream\n".encode("latin-1")
            + stream
            + b"\nendstream"
        )
        content_id = next_id
        objects[content_id] = content_obj
        next_id += 1

        page_id = next_id
        page_obj = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_id} 0 R >>"
        ).encode("latin-1")
        objects[page_id] = page_obj
        page_ids.append(page_id)
        next_id += 1

    kids = " ".join(f"{pid} 0 R" for pid in page_ids)
    objects[2] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode("latin-1")

    max_id = max(objects.keys())
    buffer = bytearray()
    buffer.extend(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = {0: 0}
    for obj_id in range(1, max_id + 1):
        offsets[obj_id] = len(buffer)
        buffer.extend(f"{obj_id} 0 obj\n".encode("latin-1"))
        buffer.extend(objects[obj_id])
        buffer.extend(b"\nendobj\n")

    xref_start = len(buffer)
    buffer.extend(f"xref\n0 {max_id + 1}\n".encode("latin-1"))
    buffer.extend(b"0000000000 65535 f \n")
    for obj_id in range(1, max_id + 1):
        buffer.extend(f"{offsets[obj_id]:010d} 00000 n \n".encode("latin-1"))
    buffer.extend(f"trailer\n<< /Size {max_id + 1} /Root 1 0 R >>\n".encode("latin-1"))
    buffer.extend(f"startxref\n{xref_start}\n%%EOF\n".encode("latin-1"))
    return bytes(buffer)


def main() -> int:
    args = parse_args()
    in_path = pathlib.Path(args.input)
    out_path = pathlib.Path(args.output)
    raw = in_path.read_text(encoding="utf-8", errors="ignore")
    wrapped: List[str] = []
    for line in raw.splitlines():
        chunks = textwrap.wrap(line, width=92) if line.strip() else [""]
        wrapped.extend(chunks)
    pages = paginate(wrapped, lines_per_page=48)
    pdf = build_pdf(pages)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(pdf)
    print(f"Wrote {out_path} ({len(pages)} page(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
