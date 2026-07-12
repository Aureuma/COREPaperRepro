#!/usr/bin/env python3
"""Fetch arXiv metadata and optionally download HTML/PDF full text."""

from __future__ import annotations

import argparse
import json
import pathlib
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Dict, Iterable, List, Tuple

ARXIV_API_URL = "https://export.arxiv.org/api/query"
USER_AGENT = "COREPaper-literature-bot/1.0 (+https://github.com/SHi-ON/COREPaper)"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="Path to literature query config JSON.")
    parser.add_argument("--max-results", type=int, default=40, help="Max results per query.")
    parser.add_argument(
        "--download-format",
        choices=("none", "html", "pdf", "both"),
        default="html",
        help="Preferred download format for full text.",
    )
    parser.add_argument("--metadata-out", required=True, help="Output JSONL path for metadata.")
    parser.add_argument("--download-dir", help="Directory to store downloaded papers.")
    parser.add_argument("--download-log", help="Output JSONL path for download events.")
    parser.add_argument("--sleep-seconds", type=float, default=0.25, help="Delay between downloads.")
    parser.add_argument("--timeout", type=int, default=30, help="HTTP timeout in seconds.")
    return parser.parse_args()


def read_query_config(path: pathlib.Path) -> List[Dict[str, str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    queries = payload.get("queries", [])
    if not queries:
        raise ValueError(f"No queries found in config: {path}")
    normalized = []
    for item in queries:
        name = item.get("name")
        arxiv_query = item.get("arxiv_query")
        if not name or not arxiv_query:
            raise ValueError(f"Malformed query item: {item}")
        normalized.append({"name": str(name), "arxiv_query": str(arxiv_query)})
    return normalized


def fetch_arxiv_feed(query: str, max_results: int, timeout: int) -> bytes:
    params = urllib.parse.urlencode(
        {
            "search_query": query,
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
    )
    request = urllib.request.Request(
        f"{ARXIV_API_URL}?{params}",
        headers={"User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def parse_feed(feed: bytes, query_name: str, query: str) -> List[Dict]:
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(feed)
    rows: List[Dict] = []

    for entry in root.findall("atom:entry", ns):
        abs_id = entry.findtext("atom:id", default="", namespaces=ns).strip()
        if not abs_id:
            continue
        arxiv_id = abs_id.split("/abs/")[-1]

        title = " ".join(entry.findtext("atom:title", default="", namespaces=ns).split())
        summary = " ".join(entry.findtext("atom:summary", default="", namespaces=ns).split())
        published = entry.findtext("atom:published", default="", namespaces=ns).strip()
        updated = entry.findtext("atom:updated", default="", namespaces=ns).strip()

        authors = []
        for author in entry.findall("atom:author", ns):
            name = author.findtext("atom:name", default="", namespaces=ns).strip()
            if name:
                authors.append(name)

        categories = []
        for category in entry.findall("atom:category", ns):
            term = category.attrib.get("term", "").strip()
            if term:
                categories.append(term)

        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        html_url = f"https://arxiv.org/html/{arxiv_id}"
        abs_url = f"https://arxiv.org/abs/{arxiv_id}"

        for link in entry.findall("atom:link", ns):
            href = link.attrib.get("href", "").strip()
            if not href:
                continue
            title_attr = link.attrib.get("title", "").strip().lower()
            if title_attr == "pdf" or href.endswith(".pdf"):
                pdf_url = href

        rows.append(
            {
                "arxiv_id": arxiv_id,
                "abs_url": abs_url,
                "pdf_url": pdf_url,
                "html_url": html_url,
                "title": title,
                "summary": summary,
                "authors": authors,
                "categories": sorted(set(categories)),
                "published": published,
                "updated": updated,
                "query_names": [query_name],
                "queries": [query],
                "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        )

    return rows


def merge_records(records: Iterable[Dict]) -> List[Dict]:
    merged: Dict[str, Dict] = {}
    for row in records:
        key = row["arxiv_id"]
        if key not in merged:
            merged[key] = row
            continue

        existing = merged[key]
        existing["query_names"] = sorted(set(existing["query_names"] + row["query_names"]))
        existing["queries"] = sorted(set(existing["queries"] + row["queries"]))
        existing["categories"] = sorted(set(existing["categories"] + row["categories"]))
        if row.get("updated", "") > existing.get("updated", ""):
            existing["updated"] = row["updated"]
            existing["published"] = row["published"]
            existing["title"] = row["title"]
            existing["summary"] = row["summary"]
            existing["authors"] = row["authors"]
            existing["abs_url"] = row["abs_url"]
            existing["pdf_url"] = row["pdf_url"]
            existing["html_url"] = row["html_url"]
            existing["retrieved_at"] = row["retrieved_at"]

    return sorted(merged.values(), key=lambda x: x.get("updated", ""), reverse=True)


def ensure_parent(path: pathlib.Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_jsonl(path: pathlib.Path, rows: Iterable[Dict]) -> None:
    ensure_parent(path)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def download_url(url: str, target: pathlib.Path, timeout: int) -> Tuple[bool, str]:
    ensure_parent(target)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = response.read()
        target.write_bytes(data)
        return True, ""
    except urllib.error.HTTPError as exc:
        return False, f"HTTP {exc.code}"
    except urllib.error.URLError as exc:
        return False, f"URL error: {exc.reason}"
    except TimeoutError:
        return False, "timeout"


def safe_id(arxiv_id: str) -> str:
    return arxiv_id.replace("/", "_")


def main() -> int:
    args = parse_args()
    config_path = pathlib.Path(args.config)
    metadata_out = pathlib.Path(args.metadata_out)
    download_dir = pathlib.Path(args.download_dir) if args.download_dir else None

    if args.download_format != "none" and download_dir is None:
        raise SystemExit("--download-dir is required unless --download-format none is used.")

    queries = read_query_config(config_path)

    collected: List[Dict] = []
    for item in queries:
        feed = fetch_arxiv_feed(item["arxiv_query"], args.max_results, args.timeout)
        collected.extend(parse_feed(feed, query_name=item["name"], query=item["arxiv_query"]))

    merged = merge_records(collected)
    write_jsonl(metadata_out, merged)

    download_events: List[Dict] = []
    if args.download_format != "none" and download_dir is not None:
        for row in merged:
            aid = row["arxiv_id"]
            paper_dir = download_dir / safe_id(aid)
            paper_dir.mkdir(parents=True, exist_ok=True)

            event: Dict[str, object] = {
                "arxiv_id": aid,
                "attempted": [],
                "downloaded": [],
            }

            def attempt(kind: str, url: str, filename: str) -> bool:
                target = paper_dir / filename
                ok, err = download_url(url, target, timeout=args.timeout)
                event["attempted"].append({"kind": kind, "url": url, "ok": ok, "error": err})
                if ok:
                    event["downloaded"].append(str(target))
                return ok

            if args.download_format == "html":
                ok = attempt("html", row["html_url"], "paper.html")
                if not ok:
                    attempt("pdf_fallback", row["pdf_url"], "paper.pdf")
            elif args.download_format == "pdf":
                attempt("pdf", row["pdf_url"], "paper.pdf")
            elif args.download_format == "both":
                attempt("html", row["html_url"], "paper.html")
                attempt("pdf", row["pdf_url"], "paper.pdf")

            download_events.append(event)
            if args.sleep_seconds > 0:
                time.sleep(args.sleep_seconds)

    download_log = pathlib.Path(args.download_log) if args.download_log else pathlib.Path(
        f"{args.metadata_out}.download-log.jsonl"
    )
    if args.download_format != "none":
        write_jsonl(download_log, download_events)

    print(f"Fetched {len(merged)} unique papers.")
    print(f"Metadata written to: {metadata_out}")
    if args.download_format != "none":
        print(f"Download log written to: {download_log}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
