#!/usr/bin/env python3
"""Extract structured literature evidence from metadata and ingested records."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
from typing import Dict, Iterable, List, Optional


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", required=True, help="Metadata JSONL path.")
    parser.add_argument("--ingested-records", required=True, help="Ingested records JSONL path.")
    parser.add_argument("--output-jsonl", required=True, help="Structured evidence JSONL output.")
    parser.add_argument("--output-md", required=True, help="Structured evidence markdown table output.")
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


def write_jsonl(path: pathlib.Path, rows: Iterable[Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_text(path: pathlib.Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def sentence_pick(text: str, keywords: List[str], max_sentences: int = 2) -> str:
    if not text:
        return ""
    chunks = re.split(r"(?<=[.!?])\s+", text)
    found: List[str] = []
    lowered_keys = [k.lower() for k in keywords]
    for sentence in chunks:
        s = sentence.strip()
        if not s:
            continue
        lower = s.lower()
        if any(k in lower for k in lowered_keys):
            found.append(s)
        if len(found) >= max_sentences:
            break
    return " ".join(found)


def first_non_empty(*values: str) -> str:
    for value in values:
        if value and value.strip():
            return value.strip()
    return ""


def map_record_by_arxiv_id(records: List[Dict]) -> Dict[str, Dict]:
    out: Dict[str, Dict] = {}
    for row in records:
        hint = str(row.get("arxiv_id_hint", "")).strip()
        if not hint:
            continue
        # Prefer HTML extraction when both HTML and PDF exist.
        existing = out.get(hint)
        if existing is None:
            out[hint] = row
            continue
        if existing.get("format") != "html" and row.get("format") == "html":
            out[hint] = row
    return out


def classify_relevance(query_names: List[str]) -> str:
    names = {q.lower() for q in query_names}
    if "robot-learning-control" in names or "manipulation-and-planning" in names:
        return "core"
    if "sim2real-and-robustness" in names:
        return "adjacent"
    return "background"


def escape_md(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def build_structured_row(meta: Dict, record: Optional[Dict]) -> Dict:
    snippets: Dict[str, str] = {}
    source_text = ""
    if record:
        snippets = record.get("section_snippets", {}) or {}
        text_path = str(record.get("text_path", "")).strip()
        source_text = read_text(pathlib.Path(text_path)) if text_path else ""

    assumptions = first_non_empty(
        sentence_pick(source_text, ["assume", "assumption", "we consider"]),
        snippets.get("method", ""),
    )
    method_core = first_non_empty(
        snippets.get("method", ""),
        sentence_pick(source_text, ["method", "approach", "framework"]),
    )
    training_setup = sentence_pick(source_text, ["train", "training", "epochs", "optimizer"])
    datasets = sentence_pick(source_text, ["dataset", "benchmark", "environment", "simulator"])
    metrics = sentence_pick(source_text, ["metric", "success rate", "accuracy", "reward", "error"])
    compute = sentence_pick(source_text, ["gpu", "cpu", "hours", "latency", "runtime"])
    failure_cases = first_non_empty(
        sentence_pick(source_text, ["failure", "limitation", "does not", "challenge"]),
        snippets.get("conclusion", ""),
    )

    return {
        "arxiv_id": meta.get("arxiv_id", ""),
        "title": meta.get("title", ""),
        "published": meta.get("published", ""),
        "updated": meta.get("updated", ""),
        "query_names": meta.get("query_names", []),
        "relevance_tag": classify_relevance(meta.get("query_names", [])),
        "assumptions": assumptions,
        "method_core": method_core,
        "training_setup": training_setup,
        "datasets": datasets,
        "metrics": metrics,
        "compute": compute,
        "failure_cases": failure_cases,
        "source_format": record.get("format", "") if record else "",
        "source_path": record.get("source_path", "") if record else "",
    }


def write_markdown(path: pathlib.Path, rows: List[Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: List[str] = []
    lines.append("# Structured Evidence Table (Auto-generated)")
    lines.append("")
    lines.append(f"- Total rows: {len(rows)}")
    lines.append("")
    lines.append("| arXiv ID | Relevance | Updated | Method Core (snippet) | Metrics (snippet) | Failure/Limitation (snippet) |")
    lines.append("|---|---|---|---|---|---|")
    for row in rows:
        lines.append(
            f"| `{escape_md(row.get('arxiv_id',''))}` | {escape_md(row.get('relevance_tag',''))} | "
            f"{escape_md(row.get('updated',''))} | {escape_md(row.get('method_core','')[:240])} | "
            f"{escape_md(row.get('metrics','')[:180])} | {escape_md(row.get('failure_cases','')[:180])} |"
        )
    if not rows:
        lines.append("| _none_ |  |  |  |  |  |")
    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    meta_rows = load_jsonl(pathlib.Path(args.metadata))
    ingested_rows = load_jsonl(pathlib.Path(args.ingested_records))
    ingested_map = map_record_by_arxiv_id(ingested_rows)

    structured = [build_structured_row(meta, ingested_map.get(str(meta.get("arxiv_id", "")))) for meta in meta_rows]
    structured = sorted(structured, key=lambda x: x.get("updated", ""), reverse=True)

    write_jsonl(pathlib.Path(args.output_jsonl), structured)
    write_markdown(pathlib.Path(args.output_md), structured)
    print(f"Structured evidence JSONL written to: {args.output_jsonl}")
    print(f"Structured evidence markdown written to: {args.output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

