#!/usr/bin/env python3
"""Audit official-code availability and subset parity for recent baseline variants.

Current scope focuses on the closest comparator `latency_aware`:
1) check official-source availability status from tracked source config,
2) collect any code-host links from metadata/raw-paper snapshots,
3) compute a software-feasible 3-task shifted subset parity report from current logs.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import pathlib
import re
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[2]
TARGET_VARIANT = "latency_aware"
REFERENCE_VARIANT = "method"
TARGET_SCENARIO = "shifted"
TARGET_TASKS = ("reach-v3", "push-v3", "button-press-v3")
CODE_HOST_PATTERNS = (
    "github.com/",
    "gitlab.com/",
    "bitbucket.org/",
    "huggingface.co/",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sources-json",
        default="config/benchmarks/recent_baseline_official_sources.json",
    )
    parser.add_argument(
        "--metadata-jsonl",
        default="data/papers/metadata/arxiv_latest.jsonl",
    )
    parser.add_argument(
        "--raw-paper-html",
        default="data/papers/raw/iros2026_lit_raw/2602.14255v1/paper.html",
    )
    parser.add_argument(
        "--results-json",
        default="output/corepaper_reports/ws3/metaworld_recent_baselines_results.json",
    )
    parser.add_argument(
        "--output-json",
        default="output/corepaper_reports/ws5/latency_aware_official_parity_audit.json",
    )
    parser.add_argument(
        "--output-md",
        default="output/corepaper_reports/ws5/latency_aware_official_parity_audit.md",
    )
    return parser.parse_args()


def _load_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl_rows(path: pathlib.Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.is_file():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def _extract_urls(text: str) -> list[str]:
    urls = re.findall(r"https?://[^\s\"'<>)}\]]+", text)
    out: list[str] = []
    seen: set[str] = set()
    for url in urls:
        normalized = url.rstrip(".,);")
        if not any(host in normalized for host in CODE_HOST_PATTERNS):
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        out.append(normalized)
    return out


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = _mean(values)
    return math.sqrt(sum((v - m) ** 2 for v in values) / (len(values) - 1))


def _cvar_bottom(values: list[float], fraction: float = 0.4) -> float:
    if not values:
        return 0.0
    k = max(1, int(round(len(values) * fraction)))
    return _mean(sorted(values)[:k])


def _ci95_delta(left: list[float], right: list[float]) -> float:
    if len(left) < 2 or len(right) < 2:
        return 0.0
    return 1.96 * math.sqrt((_std(left) ** 2 / len(left)) + (_std(right) ** 2 / len(right)))


def _build_subset_metrics(
    *,
    rows: list[dict[str, Any]],
    tasks: tuple[str, ...],
    scenario: str,
    reference_variant: str,
    comparator_variant: str,
) -> dict[str, Any]:
    by_variant: dict[str, list[float]] = {reference_variant: [], comparator_variant: []}
    by_variant_seed: dict[str, dict[int, list[float]]] = {
        reference_variant: {},
        comparator_variant: {},
    }

    allowed_tasks = set(tasks)
    for row in rows:
        if str(row.get("scenario")) != scenario:
            continue
        task = str(row.get("task"))
        if task not in allowed_tasks:
            continue
        variant = str(row.get("variant"))
        if variant not in by_variant:
            continue
        value = float(row.get("success_final", 0.0))
        seed = int(row.get("seed", 0))
        by_variant[variant].append(value)
        by_variant_seed[variant].setdefault(seed, []).append(value)

    for variant in (reference_variant, comparator_variant):
        if not by_variant[variant]:
            raise SystemExit(
                f"Missing subset rows for variant={variant}, scenario={scenario}, tasks={sorted(allowed_tasks)}"
            )

    ref = by_variant[reference_variant]
    comp = by_variant[comparator_variant]
    ref_seed_means = [_mean(vals) for _, vals in sorted(by_variant_seed[reference_variant].items())]
    comp_seed_means = [_mean(vals) for _, vals in sorted(by_variant_seed[comparator_variant].items())]
    if not ref_seed_means or not comp_seed_means:
        raise SystemExit("Missing per-seed summaries for subset parity audit.")

    return {
        "task_count": len(allowed_tasks),
        "task_names": sorted(allowed_tasks),
        "scenario": scenario,
        "reference_variant": reference_variant,
        "comparator_variant": comparator_variant,
        "n_rows_reference": len(ref),
        "n_rows_comparator": len(comp),
        "n_seed_reference": len(ref_seed_means),
        "n_seed_comparator": len(comp_seed_means),
        "reference_mean": _mean(ref),
        "comparator_mean": _mean(comp),
        "delta_mean": _mean(ref) - _mean(comp),
        "delta_mean_ci95_halfwidth": _ci95_delta(ref, comp),
        "reference_worst_seed_mean": min(ref_seed_means),
        "comparator_worst_seed_mean": min(comp_seed_means),
        "delta_worst_seed_mean": min(ref_seed_means) - min(comp_seed_means),
        "reference_cvar40_seed": _cvar_bottom(ref_seed_means, 0.4),
        "comparator_cvar40_seed": _cvar_bottom(comp_seed_means, 0.4),
        "delta_cvar40_seed": _cvar_bottom(ref_seed_means, 0.4) - _cvar_bottom(comp_seed_means, 0.4),
    }


def _write_markdown(path: pathlib.Path, payload: dict[str, Any]) -> None:
    source = payload.get("official_source", {})
    subset = payload.get("subset_metrics", {})
    assess = payload.get("parity_assessment", {})
    links = payload.get("detected_code_links", {})

    lines: list[str] = [
        "# Recent Baseline Official Parity Audit",
        "",
        f"- Generated (UTC): `{payload.get('generated_at_utc')}`",
        f"- Variant: `{payload.get('variant')}`",
        f"- Overall status: `{assess.get('status')}`",
        "",
        "## Official Source Check",
        "",
        f"- arXiv id: `{source.get('arxiv_id', 'N/A')}`",
        f"- official repo url: `{source.get('official_repo_url')}`",
        f"- availability status: `{source.get('availability_status', 'unknown')}`",
        f"- note: {source.get('notes', '')}",
        "",
        "## Code Link Discovery",
        "",
        f"- metadata links detected: `{len(links.get('metadata', []))}`",
        f"- paper-html links detected: `{len(links.get('paper_html', []))}`",
    ]
    if links.get("metadata"):
        lines.append(f"- metadata links: {', '.join(str(x) for x in links['metadata'])}")
    if links.get("paper_html"):
        lines.append(f"- paper-html links: {', '.join(str(x) for x in links['paper_html'])}")
    lines.extend(
        [
            "",
            "## 3-Task Shifted Subset Parity",
            "",
            (
                f"- subset: scenario=`{subset.get('scenario')}`, tasks=`{', '.join(subset.get('task_names', []))}`"
            ),
            (
                f"- mean: {subset.get('reference_variant')}={subset.get('reference_mean', 0.0):.4f}, "
                f"{subset.get('comparator_variant')}={subset.get('comparator_mean', 0.0):.4f}, "
                f"delta={subset.get('delta_mean', 0.0):+.4f} (CI95 halfwidth "
                f"{subset.get('delta_mean_ci95_halfwidth', 0.0):.4f})"
            ),
            (
                f"- worst-seed: {subset.get('reference_variant')}={subset.get('reference_worst_seed_mean', 0.0):.4f}, "
                f"{subset.get('comparator_variant')}={subset.get('comparator_worst_seed_mean', 0.0):.4f}, "
                f"delta={subset.get('delta_worst_seed_mean', 0.0):+.4f}"
            ),
            (
                f"- CVaR40-seed: {subset.get('reference_variant')}={subset.get('reference_cvar40_seed', 0.0):.4f}, "
                f"{subset.get('comparator_variant')}={subset.get('comparator_cvar40_seed', 0.0):.4f}, "
                f"delta={subset.get('delta_cvar40_seed', 0.0):+.4f}"
            ),
            "",
            "## Assessment",
            "",
            f"- reason: {assess.get('reasoning', '')}",
        ]
    )
    residual = assess.get("residual_risks", [])
    if isinstance(residual, list) and residual:
        lines.append("- residual risks:")
        for risk in residual:
            lines.append(f"  - {risk}")
    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    sources_path = ROOT / args.sources_json
    metadata_path = ROOT / args.metadata_jsonl
    raw_html_path = ROOT / args.raw_paper_html
    results_path = ROOT / args.results_json
    output_json_path = ROOT / args.output_json
    output_md_path = ROOT / args.output_md

    sources_payload = _load_json(sources_path)
    source_info = sources_payload.get("sources", {}).get(TARGET_VARIANT)
    if not isinstance(source_info, dict):
        raise SystemExit(f"Missing source config for variant '{TARGET_VARIANT}' in {sources_path}")

    metadata_rows = _load_jsonl_rows(metadata_path)
    by_arxiv = {
        str(row.get("arxiv_id")): row
        for row in metadata_rows
        if isinstance(row, dict) and row.get("arxiv_id")
    }
    arxiv_id = str(source_info.get("arxiv_id", "")).strip()
    meta_row = by_arxiv.get(arxiv_id, {})

    metadata_text = json.dumps(meta_row, ensure_ascii=False) if meta_row else ""
    metadata_links = _extract_urls(metadata_text)
    html_text = raw_html_path.read_text(encoding="utf-8", errors="replace") if raw_html_path.is_file() else ""
    html_links = _extract_urls(html_text)

    results_payload = _load_json(results_path)
    episodes = results_payload.get("episodes", [])
    if not isinstance(episodes, list):
        raise SystemExit(f"Invalid results payload: expected list at {results_path}::episodes")
    subset_metrics = _build_subset_metrics(
        rows=episodes,
        tasks=TARGET_TASKS,
        scenario=TARGET_SCENARIO,
        reference_variant=REFERENCE_VARIANT,
        comparator_variant=TARGET_VARIANT,
    )

    source_status = str(source_info.get("availability_status", "")).strip().lower()
    has_official_repo = bool(source_info.get("official_repo_url"))
    floor_positive = (
        float(subset_metrics.get("delta_worst_seed_mean", 0.0)) >= 0.0
        and float(subset_metrics.get("delta_cvar40_seed", 0.0)) >= 0.0
    )

    if has_official_repo:
        status = "official_repo_declared_subset_verified"
        reasoning = "Official repository URL is declared; subset parity check executed from current benchmark logs."
    elif source_status in {"not_found_public_release", "no_public_code"}:
        status = "no_public_repo_subset_verified"
        reasoning = (
            "No public official repository is currently tracked for latency_aware; "
            "software-feasible subset parity check is provided as the reproducible fallback."
        )
    else:
        status = "source_status_unresolved_subset_verified"
        reasoning = (
            "Official repository availability is unresolved in source config; "
            "subset parity check executed while preserving explicit uncertainty."
        )

    residual_risks: list[str] = []
    if not has_official_repo:
        residual_risks.append(
            "Official-code parity cannot be fully closed until an upstream public repository/checkpoint is available."
        )
    if not floor_positive:
        residual_risks.append("Subset floor deltas are not uniformly positive; monitor next-cycle reruns.")

    payload: dict[str, Any] = {
        "generated_at_utc": dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "variant": TARGET_VARIANT,
        "official_source": source_info,
        "detected_code_links": {
            "metadata": metadata_links,
            "paper_html": html_links,
        },
        "subset_metrics": subset_metrics,
        "parity_assessment": {
            "status": status,
            "reasoning": reasoning,
            "subset_floor_positive": floor_positive,
            "residual_risks": residual_risks,
        },
    }

    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    output_md_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    _write_markdown(output_md_path, payload)
    print(f"Wrote {output_json_path.relative_to(ROOT)}")
    print(f"Wrote {output_md_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
