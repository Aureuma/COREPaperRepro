# Literature Data Layout

- `raw/`: downloaded paper files (arXiv HTML preferred, PDF fallback).
- `metadata/`: JSONL snapshots of discovered papers.
- `ingested/`: extracted text and ingestion records for downstream review.

Use immutable weekly snapshot names for reproducibility, e.g.:

- `metadata/arxiv_2026-02-17.jsonl`
- `raw/arxiv_2026-02-17/<arxiv_id>/paper.html`
- `ingested/arxiv_2026-02-17_records.jsonl`

