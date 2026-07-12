#!/usr/bin/env python3
"""Run a multi-round Gemini<->Claude counsel critique and emit consensus output.

Inspiration: https://github.com/karpathy/llm-council

This orchestrator executes both provider critique runners in batch mode only,
then passes each model a compact summary of the peer model's prior-round
critique. The loop stops early once consensus criteria are satisfied.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PY = sys.executable
COUNCIL_INSPIRATION_URL = "https://github.com/karpathy/llm-council"

DEFAULT_GEMINI_MODEL = os.getenv(
    "COREPAPER_GEMINI_MODEL_NAME",
    os.getenv("RM_GEMINI_MODEL_NAME", "gemini-3.1-pro-preview"),
)
DEFAULT_GEMINI_SCHEMA_MODE = os.getenv("PIPELINE_GEMINI_SCHEMA_MODE", "compact")
DEFAULT_CLAUDE_MODEL = os.getenv(
    "COREPAPER_BEDROCK_MODEL_ID",
    os.getenv("BEDROCK_MODEL_ID", "us.anthropic.claude-opus-4-6-v1"),
)
DEFAULT_CLAUDE_BACKEND = os.getenv("PIPELINE_CLAUDE_BACKEND", "boto3")
DEFAULT_CLAUDE_SCHEMA_MODE = os.getenv("PIPELINE_CLAUDE_SCHEMA_MODE", "compact")


def _safe_env_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


DEFAULT_GEMINI_MAX_TEX_CHARS = max(8_000, _safe_env_int("COREPAPER_COUNSEL_GEMINI_MAX_TEX_CHARS", 50_000))
DEFAULT_GEMINI_MAX_PLAN_CHARS = max(6_000, _safe_env_int("COREPAPER_COUNSEL_GEMINI_MAX_PLAN_CHARS", 30_000))
DEFAULT_GEMINI_MAX_PEER_CONTEXT_CHARS = max(
    1_000,
    _safe_env_int("COREPAPER_COUNSEL_GEMINI_MAX_PEER_CONTEXT_CHARS", 8_000),
)
HARD_COUNSEL_ROUND_CAP = 5
_MAX_COUNSEL_ROUNDS_RAW = os.getenv("COREPAPER_COUNSEL_MAX_ROUNDS", str(HARD_COUNSEL_ROUND_CAP)).strip()
try:
    _MAX_COUNSEL_ROUNDS = int(_MAX_COUNSEL_ROUNDS_RAW)
except ValueError:
    _MAX_COUNSEL_ROUNDS = HARD_COUNSEL_ROUND_CAP
MAX_COUNSEL_ROUNDS = max(1, min(HARD_COUNSEL_ROUND_CAP, _MAX_COUNSEL_ROUNDS))
DEFAULT_COUNSEL_ROUNDS = MAX_COUNSEL_ROUNDS
DEFAULT_IMPROVEMENT_DIRECTIVE = os.getenv(
    "COREPAPER_COUNSEL_IMPROVEMENT_DIRECTIVE",
    (
        "Critique from uncommon reviewer angles and fully stress-test acceptance risk. "
        "Prioritize cross-artifact contradiction hunting (abstract/introduction/results/conclusion vs tables/figures/macros), "
        "statistical validity under multiplicity, baseline fairness and parity assumptions, theorem-assumption tightness, "
        "notation consistency, visualization interpretability/accessibility, and reproducibility gaps. "
        "Prefer desk-reject and high-impact issues first, with executable repo-level fixes and concrete validation checks."
    ),
)

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "its",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "we",
    "with",
}


def _resolve_rounds(requested: int) -> int:
    if requested < 1:
        raise ValueError("rounds must be >= 1")
    return min(requested, MAX_COUNSEL_ROUNDS)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(_read_text(path))


def _normalize_tag(tag: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9_.-]+", "-", tag.strip())
    return clean.strip("-._")


def _today_stamp() -> str:
    return dt.date.today().isoformat()


def _auto_run_tag() -> str:
    now = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    return f"counsel-{now}"


def _extract_findings(payload: dict[str, Any]) -> list[dict[str, Any]]:
    findings = payload.get("critical_findings")
    if isinstance(findings, list):
        return [item for item in findings if isinstance(item, dict)]
    top = payload.get("top_findings")
    if isinstance(top, list):
        return [item for item in top if isinstance(item, dict)]
    return []


def _latest_critique_path(output_dir: Path, pattern: str) -> Path | None:
    matches = sorted(output_dir.glob(pattern), key=lambda p: p.stat().st_mtime)
    filtered: list[Path] = []
    for path in matches:
        name = path.name
        if name.endswith("_raw.json") or name.endswith("_request.json"):
            continue
        filtered.append(path)
    if not filtered:
        return None
    return filtered[-1]


def _resolve_parsed_path(output_dir: Path, expected: Path, pattern: str) -> Path | None:
    if expected.exists():
        return expected
    return _latest_critique_path(output_dir, pattern)


def _extract_actions(payload: dict[str, Any]) -> list[str]:
    actions: list[str] = []
    backlog = payload.get("priority_backlog")
    if isinstance(backlog, list):
        for row in backlog:
            if isinstance(row, dict):
                action = row.get("action")
                if isinstance(action, str) and action.strip():
                    actions.append(action.strip())
    next_actions = payload.get("next_actions")
    if isinstance(next_actions, list):
        for row in next_actions:
            if isinstance(row, str) and row.strip():
                actions.append(row.strip())
    seen: set[str] = set()
    deduped: list[str] = []
    for item in actions:
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _extract_risks(payload: dict[str, Any]) -> list[str]:
    risks = payload.get("residual_risks")
    if not isinstance(risks, list):
        return []
    out: list[str] = []
    for row in risks:
        if isinstance(row, str) and row.strip():
            out.append(row.strip())
    return out


def _risk_score(payload: dict[str, Any]) -> float | None:
    raw = payload.get("acceptance_risk_score_0_to_10")
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _verdict_bucket(payload: dict[str, Any]) -> str:
    verdict = str(payload.get("overall_verdict", "")).lower()
    if not verdict.strip():
        return "unknown"
    if "strong accept" in verdict or "accept" in verdict:
        return "accept"
    if "near-ready" in verdict or "near ready" in verdict:
        return "near-ready"
    if "reject" in verdict:
        return "reject"
    if "risk" in verdict:
        return "risk"
    return "unknown"


def _high_severity_count(payload: dict[str, Any]) -> int:
    count = 0
    for row in _extract_findings(payload):
        sev = str(row.get("severity", "")).lower()
        if sev in {"critical", "high"}:
            count += 1
    return count


def _tokenize(text: str) -> set[str]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return {tok for tok in tokens if len(tok) >= 3 and tok not in STOPWORDS}


def _finding_topic_sets(payload: dict[str, Any]) -> list[set[str]]:
    topics: list[set[str]] = []
    for row in _extract_findings(payload):
        issue = str(row.get("issue", ""))
        fix = str(row.get("fix", ""))
        tok = _tokenize(f"{issue} {fix}")
        if tok:
            topics.append(tok)
    return topics


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    if union == 0:
        return 0.0
    return inter / union


def _max_topic_overlap(a_topics: list[set[str]], b_topics: list[set[str]]) -> float:
    if not a_topics or not b_topics:
        return 0.0
    best = 0.0
    for a in a_topics:
        for b in b_topics:
            score = _jaccard(a, b)
            if score > best:
                best = score
    return best


def _pair_key(left: str, right: str) -> str:
    a, b = sorted((left, right))
    return f"{a}|{b}"


def evaluate_council_consensus(
    council_payloads: dict[str, dict[str, Any]],
    *,
    max_risk_delta: float,
    min_topic_overlap: float,
) -> dict[str, Any]:
    seats = {name: payload for name, payload in council_payloads.items() if isinstance(payload, dict)}
    seat_names = sorted(seats)

    risks = {name: _risk_score(payload) for name, payload in seats.items()}
    topic_sets = {name: _finding_topic_sets(payload) for name, payload in seats.items()}
    verdict_buckets = {name: _verdict_bucket(payload) for name, payload in seats.items()}
    severity_counts = {name: _high_severity_count(payload) for name, payload in seats.items()}

    pairwise_risk_deltas: dict[str, float] = {}
    pairwise_topic_overlap: dict[str, float] = {}
    for idx, left in enumerate(seat_names):
        for right in seat_names[idx + 1 :]:
            key = _pair_key(left, right)
            pairwise_topic_overlap[key] = _max_topic_overlap(topic_sets[left], topic_sets[right])
            left_risk = risks.get(left)
            right_risk = risks.get(right)
            if left_risk is not None and right_risk is not None:
                pairwise_risk_deltas[key] = abs(left_risk - right_risk)

    risk_delta: float | None = None
    if pairwise_risk_deltas:
        risk_delta = max(pairwise_risk_deltas.values())

    topic_overlap = 1.0
    if pairwise_topic_overlap:
        topic_overlap = min(pairwise_topic_overlap.values())

    known_buckets = {bucket for bucket in verdict_buckets.values() if bucket != "unknown"}
    verdict_aligned = len(known_buckets) <= 1

    severity_gap = 0
    if severity_counts:
        severity_gap = max(severity_counts.values()) - min(severity_counts.values())
    severity_aligned = severity_gap <= 1

    findings_sparse = True
    if topic_sets:
        findings_sparse = max(len(topics) for topics in topic_sets.values()) <= 1
    overlap_aligned = topic_overlap >= min_topic_overlap or findings_sparse
    risk_aligned = (risk_delta is None) or (risk_delta <= max_risk_delta)

    reached = risk_aligned and verdict_aligned and severity_aligned and overlap_aligned
    return {
        "consensus_reached": reached,
        "risk_aligned": risk_aligned,
        "risk_delta": risk_delta,
        "verdict_aligned": verdict_aligned,
        "severity_aligned": severity_aligned,
        "severity_gap": severity_gap,
        "topic_overlap": topic_overlap,
        "overlap_aligned": overlap_aligned,
        "verdict_buckets": verdict_buckets,
        "seat_names": seat_names,
        "pairwise_risk_deltas": pairwise_risk_deltas,
        "pairwise_topic_overlap": pairwise_topic_overlap,
    }


def evaluate_consensus(
    gemini_payload: dict[str, Any],
    claude_payload: dict[str, Any],
    *,
    max_risk_delta: float,
    min_topic_overlap: float,
) -> dict[str, Any]:
    return evaluate_council_consensus(
        {"gemini": gemini_payload, "claude": claude_payload},
        max_risk_delta=max_risk_delta,
        min_topic_overlap=min_topic_overlap,
    )


def _compact_findings(payload: dict[str, Any], *, limit: int = 4) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for row in _extract_findings(payload)[:limit]:
        out.append(
            {
                "id": str(row.get("id", ""))[:64],
                "severity": str(row.get("severity", ""))[:16],
                "issue": str(row.get("issue", ""))[:240],
                "fix": str(row.get("fix", ""))[:240],
            }
        )
    return out


def _build_peer_context(
    *,
    source_model: str,
    round_index: int,
    critique_payload: dict[str, Any],
    consensus_snapshot: dict[str, Any] | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "source_model": source_model,
        "round_index": round_index,
        "overall_verdict": critique_payload.get("overall_verdict"),
        "acceptance_risk_score_0_to_10": critique_payload.get("acceptance_risk_score_0_to_10"),
        "strengths": critique_payload.get("strengths", []),
        "findings": _compact_findings(critique_payload),
        "suggested_actions": _extract_actions(critique_payload)[:6],
        "residual_risks": _extract_risks(critique_payload)[:6],
    }
    if consensus_snapshot is not None:
        payload["consensus_snapshot"] = consensus_snapshot
    return payload


def _run_cmd(cmd: list[str], *, log_path: Path) -> tuple[int, str]:
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)
    log = []
    log.append(f"$ {' '.join(cmd)}")
    if proc.stdout:
        log.append("\n[stdout]\n" + proc.stdout)
    if proc.stderr:
        log.append("\n[stderr]\n" + proc.stderr)
    log_path.write_text("\n".join(log).strip() + "\n", encoding="utf-8")
    return proc.returncode, log_path.name


def _run_gemini_batch(
    *,
    paper_pdf: Path,
    paper_tex: Path,
    plan_md: Path,
    output_dir: Path,
    model: str,
    schema_mode: str,
    max_output_tokens: int,
    improvement_directive: str,
    tag: str,
    peer_context_json: Path | None,
    max_tex_chars: int = DEFAULT_GEMINI_MAX_TEX_CHARS,
    max_plan_chars: int = DEFAULT_GEMINI_MAX_PLAN_CHARS,
    max_peer_context_chars: int = DEFAULT_GEMINI_MAX_PEER_CONTEXT_CHARS,
) -> tuple[int, Path, Path]:
    manifest_path = output_dir / f"corepaper_counsel_gemini_manifest_{tag}.json"
    job: dict[str, Any] = {
        "paper_pdf": str(paper_pdf),
        "paper_tex": str(paper_tex),
        "plan_md": str(plan_md),
        "output_dir": str(output_dir),
        "model": model,
        "schema_mode": schema_mode,
        "max_output_tokens": max_output_tokens,
        "improvement_directive": improvement_directive,
        "max_tex_chars": max_tex_chars,
        "max_plan_chars": max_plan_chars,
        "max_peer_context_chars": max_peer_context_chars,
        "tag": tag,
    }
    if peer_context_json is not None:
        job["peer_context_json"] = str(peer_context_json)
    _write_json(manifest_path, {"jobs": [job]})
    log_path = output_dir / f"corepaper_counsel_gemini_{tag}.log"
    cmd = [
        PY,
        "scripts/review_readiness/run_gemini_critique.py",
        "--batch-manifest",
        str(manifest_path),
        "--fail-fast",
    ]
    code, _ = _run_cmd(cmd, log_path=log_path)
    expected = output_dir / f"corepaper_gemini_critique_{_today_stamp()}_{tag}.json"
    return code, expected, log_path


def _run_claude_batch(
    *,
    paper_pdf: Path,
    paper_tex: Path,
    plan_md: Path,
    output_dir: Path,
    model: str,
    region: str,
    backend: str,
    schema_mode: str,
    max_output_tokens: int,
    improvement_directive: str,
    tag: str,
    peer_context_json: Path | None,
) -> tuple[int, Path, Path]:
    manifest_path = output_dir / f"corepaper_counsel_claude_manifest_{tag}.json"
    job: dict[str, Any] = {
        "paper_pdf": str(paper_pdf),
        "paper_tex": str(paper_tex),
        "plan_md": str(plan_md),
        "output_dir": str(output_dir),
        "model": model,
        "region": region,
        "backend": backend,
        "schema_mode": schema_mode,
        "max_output_tokens": max_output_tokens,
        "improvement_directive": improvement_directive,
        "tag": tag,
    }
    if peer_context_json is not None:
        job["peer_context_json"] = str(peer_context_json)
    _write_json(manifest_path, {"jobs": [job]})
    log_path = output_dir / f"corepaper_counsel_claude_{tag}.log"
    cmd = [
        PY,
        "scripts/review_readiness/run_bedrock_claude_critique.py",
        "--batch-manifest",
        str(manifest_path),
        "--fail-fast",
    ]
    code, _ = _run_cmd(cmd, log_path=log_path)
    expected = output_dir / f"corepaper_bedrock_claude_critique_{_today_stamp()}_{tag}.json"
    return code, expected, log_path


def _merge_consensus_findings(
    gemini_payload: dict[str, Any],
    claude_payload: dict[str, Any],
    *,
    limit: int = 8,
) -> list[dict[str, Any]]:
    return _merge_consensus_findings_from_sources(
        {"gemini": gemini_payload, "claude": claude_payload},
        limit=limit,
    )


def _merge_consensus_findings_from_sources(
    source_payloads: dict[str, dict[str, Any]],
    *,
    limit: int = 8,
) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    for source, payload in source_payloads.items():
        for row in _compact_findings(payload):
            key = f"{row.get('issue', '').strip().lower()}|{row.get('fix', '').strip().lower()}"
            if not key.strip("|"):
                continue
            if any(existing.get("key") == key for existing in merged):
                continue
            merged.append({"source": source, "key": key, **row})
            if len(merged) >= limit:
                break
        if len(merged) >= limit:
            break
    for row in merged:
        row.pop("key", None)
    return merged


def _dedupe_lower(items: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        key = item.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(item.strip())
    return out


def _build_round_peer_context_payload(
    *,
    peer_context: dict[str, Any],
    local_member_label: str | None,
    local_member_payload: dict[str, Any] | None,
    round_index: int,
    consensus_snapshot: dict[str, Any] | None,
) -> dict[str, Any]:
    if not local_member_label or local_member_payload is None:
        return peer_context
    local_peer_context = _build_peer_context(
        source_model=local_member_label,
        round_index=round_index,
        critique_payload=local_member_payload,
        consensus_snapshot=consensus_snapshot,
    )
    return {
        "peer_round_context": peer_context,
        "additional_council_members": [local_peer_context],
        "instruction": (
            "Treat additional_council_members as extra council votes. "
            "Address or rebut each high-severity finding explicitly."
        ),
    }


def _write_markdown_summary(path: Path, *, consensus: dict[str, Any]) -> None:
    lines: list[str] = [
        f"# LLM Counsel Critique Summary ({dt.date.today().isoformat()})",
        "",
        "## Verdict",
        "",
        f"- Consensus reached: `{consensus.get('consensus_reached')}`",
        f"- Final risk (0-10): `{consensus.get('final_acceptance_risk_score_0_to_10')}`",
        f"- Final verdict: `{consensus.get('final_overall_verdict')}`",
        "",
        "## Round Metrics",
        "",
    ]
    rounds = consensus.get("rounds", [])
    if isinstance(rounds, list) and rounds:
        for row in rounds:
            if not isinstance(row, dict):
                continue
            metrics = row.get("consensus_metrics", {})
            lines.append(
                "- "
                + f"Round {row.get('round_index')}: reached={metrics.get('consensus_reached')}, "
                + f"risk_delta={metrics.get('risk_delta')}, "
                + f"topic_overlap={metrics.get('topic_overlap')}"
            )
    else:
        lines.append("- No rounds recorded.")
    lines.extend(["", "## Final Findings", ""])
    findings = consensus.get("consensus_findings", [])
    if isinstance(findings, list) and findings:
        for row in findings:
            if not isinstance(row, dict):
                continue
            lines.append(
                f"- `{row.get('id', 'NA')}` ({row.get('severity', 'NA')}, {row.get('source', 'NA')}): {row.get('issue', '')}"
            )
            lines.append(f"  - Fix: {row.get('fix', '')}")
    else:
        lines.append("- No merged findings listed.")
    lines.extend(["", "## Final Actions", ""])
    actions = consensus.get("consensus_actions", [])
    if isinstance(actions, list) and actions:
        for row in actions:
            lines.append(f"- {row}")
    else:
        lines.append("- No actions listed.")
    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def _build_stale_fallback_consensus(
    *,
    output_dir: Path,
    run_tag: str,
    reason: str,
    criteria: dict[str, Any],
    local_member_label: str | None = None,
    local_member_payload: dict[str, Any] | None = None,
    local_member_source_path: Path | None = None,
) -> tuple[dict[str, Any], Path, Path] | None:
    latest_gemini = _latest_critique_path(output_dir, "corepaper_gemini_critique_*.json")
    latest_claude = _latest_critique_path(output_dir, "corepaper_bedrock_claude_critique_*.json")
    if latest_gemini is None or latest_claude is None:
        return None

    gemini_payload = _read_json(latest_gemini)
    claude_payload = _read_json(latest_claude)
    council_payloads: dict[str, dict[str, Any]] = {
        "gemini": gemini_payload,
        "claude": claude_payload,
    }
    if local_member_label and local_member_payload is not None:
        council_payloads[local_member_label] = local_member_payload

    metrics = evaluate_council_consensus(
        council_payloads,
        max_risk_delta=float(criteria["max_risk_delta"]),
        min_topic_overlap=float(criteria["min_topic_overlap"]),
    )

    risk_values = [_risk_score(payload) for payload in council_payloads.values()]
    risk_values = [x for x in risk_values if x is not None]
    final_risk = round(sum(risk_values) / len(risk_values), 3) if risk_values else None

    consensus_actions = _dedupe_lower(
        [action for payload in council_payloads.values() for action in _extract_actions(payload)]
    )
    consensus_risks = _dedupe_lower(
        [risk for payload in council_payloads.values() for risk in _extract_risks(payload)]
    )

    fallback_payload = {
        "mode": "llm_counsel_stale_fallback",
        "inspiration": {
            "name": "llm-council",
            "url": COUNCIL_INSPIRATION_URL,
        },
        "provider_invocation_policy": {
            "batch_mode_only": True,
            "details": "Council invokes provider runners only via batch manifests.",
        },
        "consensus_reached": bool(metrics.get("consensus_reached")),
        "final_overall_verdict": "Fallback consensus from latest available provider critiques",
        "final_acceptance_risk_score_0_to_10": final_risk,
        "fallback_reason": reason,
        "consensus_criteria": criteria,
        "council_seats": list(council_payloads.keys()),
        "final_round_metrics": metrics,
        "consensus_findings": _merge_consensus_findings_from_sources(council_payloads),
        "consensus_actions": consensus_actions[:12],
        "consensus_residual_risks": consensus_risks[:12],
        "rounds": [],
        "fallback_source_artifacts": {
            "gemini_parsed_path": str(latest_gemini),
            "claude_parsed_path": str(latest_claude),
        },
    }
    if local_member_label and local_member_payload is not None:
        fallback_payload["local_member"] = {
            "label": local_member_label,
            "source_path": str(local_member_source_path) if local_member_source_path else "inline",
        }
        fallback_payload["fallback_source_artifacts"]["local_member_source"] = (
            str(local_member_source_path) if local_member_source_path else "inline"
        )

    stamp = _today_stamp()
    parsed_path = output_dir / f"corepaper_llm_counsel_critique_{stamp}_{run_tag}_fallback.json"
    summary_path = output_dir / f"corepaper_llm_counsel_critique_{stamp}_{run_tag}_fallback.md"
    return fallback_payload, parsed_path, summary_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper-pdf", type=Path, default=Path("paper/build/manuscript.pdf"))
    parser.add_argument("--paper-tex", type=Path, default=Path("paper/manuscript.tex"))
    parser.add_argument("--plan-md", type=Path, default=Path("docs/plan.md"))
    parser.add_argument("--output-dir", type=Path, default=Path("output/corepaper_reports/review_readiness"))
    parser.add_argument("--tag", default="", help="Optional run tag suffix.")
    parser.add_argument(
        "--rounds",
        type=int,
        default=DEFAULT_COUNSEL_ROUNDS,
        help=f"Maximum counsel rounds (hard-capped at {MAX_COUNSEL_ROUNDS}).",
    )
    parser.add_argument("--max-risk-delta", type=float, default=1.5)
    parser.add_argument("--min-topic-overlap", type=float, default=0.20)
    parser.add_argument("--gemini-model", default=DEFAULT_GEMINI_MODEL)
    parser.add_argument("--gemini-schema-mode", choices=("full", "compact"), default=DEFAULT_GEMINI_SCHEMA_MODE)
    parser.add_argument("--gemini-max-output-tokens", type=int, default=8192)
    parser.add_argument("--gemini-max-tex-chars", type=int, default=DEFAULT_GEMINI_MAX_TEX_CHARS)
    parser.add_argument("--gemini-max-plan-chars", type=int, default=DEFAULT_GEMINI_MAX_PLAN_CHARS)
    parser.add_argument("--gemini-max-peer-context-chars", type=int, default=DEFAULT_GEMINI_MAX_PEER_CONTEXT_CHARS)
    parser.add_argument("--claude-model", default=DEFAULT_CLAUDE_MODEL)
    parser.add_argument("--claude-region", default=os.getenv("COREPAPER_AWS_DEFAULT_REGION", "us-east-1"))
    parser.add_argument("--claude-backend", choices=("auto", "si", "boto3"), default=DEFAULT_CLAUDE_BACKEND)
    parser.add_argument("--claude-schema-mode", choices=("full", "compact"), default=DEFAULT_CLAUDE_SCHEMA_MODE)
    parser.add_argument("--claude-max-output-tokens", type=int, default=4096)
    parser.add_argument(
        "--improvement-directive",
        default=DEFAULT_IMPROVEMENT_DIRECTIVE,
        help="Optional high-priority instruction to bias critique toward substantial paper improvements.",
    )
    parser.add_argument(
        "--council-local-opinion-json",
        type=Path,
        default=None,
        help=(
            "Optional local council-member critique JSON (Codex opinion). "
            "When provided, this seat is included in consensus scoring and peer context."
        ),
    )
    parser.add_argument(
        "--council-local-opinion-label",
        default="codex",
        help="Label for the local council-member seat (default: codex).",
    )
    parser.add_argument(
        "--allow-stale-fallback",
        action="store_true",
        help=(
            "If a live provider round fails, build consensus from latest available "
            "Gemini/Claude critique artifacts in output-dir."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        max_rounds = _resolve_rounds(int(args.rounds))
    except ValueError:
        print("--rounds must be >= 1.", file=sys.stderr)
        return 2
    if max_rounds < args.rounds:
        print(
            f"[counsel] requested rounds={args.rounds} exceeds cap={MAX_COUNSEL_ROUNDS}; using {max_rounds}.",
            file=sys.stderr,
        )

    for req in (args.paper_pdf, args.paper_tex, args.plan_md):
        if not req.exists():
            print(f"Missing required file: {req}", file=sys.stderr)
            return 2

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    run_tag = _normalize_tag(args.tag) if args.tag.strip() else _auto_run_tag()
    if not run_tag:
        print("Invalid --tag value.", file=sys.stderr)
        return 2

    local_member_payload: dict[str, Any] | None = None
    local_member_source_path: Path | None = None
    local_member_label = _normalize_tag(str(args.council_local_opinion_label or "codex")) or "codex"
    if args.council_local_opinion_json is not None:
        if not args.council_local_opinion_json.exists():
            print(f"Missing local council opinion JSON: {args.council_local_opinion_json}", file=sys.stderr)
            return 2
        local_member_payload = _read_json(args.council_local_opinion_json)
        local_member_source_path = args.council_local_opinion_json

    peer_for_gemini: Path | None = None
    peer_for_claude: Path | None = None
    round_records: list[dict[str, Any]] = []
    last_gemini_payload: dict[str, Any] | None = None
    last_claude_payload: dict[str, Any] | None = None
    final_metrics: dict[str, Any] | None = None

    for round_index in range(1, max_rounds + 1):
        gemini_tag = f"{run_tag}_r{round_index:02d}_gemini"
        claude_tag = f"{run_tag}_r{round_index:02d}_claude"

        gemini_code, gemini_parsed_path, gemini_log_path = _run_gemini_batch(
            paper_pdf=args.paper_pdf,
            paper_tex=args.paper_tex,
            plan_md=args.plan_md,
            output_dir=output_dir,
            model=args.gemini_model,
            schema_mode=args.gemini_schema_mode,
            max_output_tokens=args.gemini_max_output_tokens,
            improvement_directive=args.improvement_directive,
            tag=gemini_tag,
            peer_context_json=peer_for_gemini,
            max_tex_chars=args.gemini_max_tex_chars,
            max_plan_chars=args.gemini_max_plan_chars,
            max_peer_context_chars=args.gemini_max_peer_context_chars,
        )
        if gemini_code != 0:
            reason = (
                f"Gemini counsel round {round_index} failed (code={gemini_code}). "
                f"See log: {gemini_log_path}"
            )
            if args.allow_stale_fallback:
                fallback = _build_stale_fallback_consensus(
                    output_dir=output_dir,
                    run_tag=run_tag,
                    reason=reason,
                    criteria={
                        "max_risk_delta": args.max_risk_delta,
                        "min_topic_overlap": args.min_topic_overlap,
                        "max_rounds": max_rounds,
                    },
                    local_member_label=local_member_label if local_member_payload is not None else None,
                    local_member_payload=local_member_payload,
                    local_member_source_path=local_member_source_path,
                )
                if fallback is None:
                    print(reason, file=sys.stderr)
                    print("Stale fallback requested but no prior provider critiques were found.", file=sys.stderr)
                    return 1
                payload, parsed_path, summary_path = fallback
                _write_json(parsed_path, payload)
                _write_markdown_summary(summary_path, consensus=payload)
                print(f"[counsel] fallback mode enabled. Reason: {reason}")
                print(f"Wrote counsel fallback JSON: {parsed_path}")
                print(f"Wrote counsel fallback summary: {summary_path}")
                return 0
            print(reason, file=sys.stderr)
            return 1
        resolved_gemini = _resolve_parsed_path(
            output_dir,
            gemini_parsed_path,
            f"corepaper_gemini_critique_*_{gemini_tag}.json",
        )
        if resolved_gemini is None:
            print(f"Expected Gemini parsed critique not found: {gemini_parsed_path}", file=sys.stderr)
            return 1
        gemini_parsed_path = resolved_gemini

        claude_code, claude_parsed_path, claude_log_path = _run_claude_batch(
            paper_pdf=args.paper_pdf,
            paper_tex=args.paper_tex,
            plan_md=args.plan_md,
            output_dir=output_dir,
            model=args.claude_model,
            region=args.claude_region,
            backend=args.claude_backend,
            schema_mode=args.claude_schema_mode,
            max_output_tokens=args.claude_max_output_tokens,
            improvement_directive=args.improvement_directive,
            tag=claude_tag,
            peer_context_json=peer_for_claude,
        )
        if claude_code != 0:
            reason = (
                f"Claude counsel round {round_index} failed (code={claude_code}). "
                f"See log: {claude_log_path}"
            )
            if args.allow_stale_fallback:
                fallback = _build_stale_fallback_consensus(
                    output_dir=output_dir,
                    run_tag=run_tag,
                    reason=reason,
                    criteria={
                        "max_risk_delta": args.max_risk_delta,
                        "min_topic_overlap": args.min_topic_overlap,
                        "max_rounds": max_rounds,
                    },
                    local_member_label=local_member_label if local_member_payload is not None else None,
                    local_member_payload=local_member_payload,
                    local_member_source_path=local_member_source_path,
                )
                if fallback is None:
                    print(reason, file=sys.stderr)
                    print("Stale fallback requested but no prior provider critiques were found.", file=sys.stderr)
                    return 1
                payload, parsed_path, summary_path = fallback
                _write_json(parsed_path, payload)
                _write_markdown_summary(summary_path, consensus=payload)
                print(f"[counsel] fallback mode enabled. Reason: {reason}")
                print(f"Wrote counsel fallback JSON: {parsed_path}")
                print(f"Wrote counsel fallback summary: {summary_path}")
                return 0
            print(reason, file=sys.stderr)
            return 1
        resolved_claude = _resolve_parsed_path(
            output_dir,
            claude_parsed_path,
            f"corepaper_bedrock_claude_critique_*_{claude_tag}.json",
        )
        if resolved_claude is None:
            print(f"Expected Claude parsed critique not found: {claude_parsed_path}", file=sys.stderr)
            return 1
        claude_parsed_path = resolved_claude

        gemini_payload = _read_json(gemini_parsed_path)
        claude_payload = _read_json(claude_parsed_path)
        council_payloads: dict[str, dict[str, Any]] = {
            "gemini": gemini_payload,
            "claude": claude_payload,
        }
        if local_member_payload is not None:
            council_payloads[local_member_label] = local_member_payload

        metrics = evaluate_council_consensus(
            council_payloads,
            max_risk_delta=args.max_risk_delta,
            min_topic_overlap=args.min_topic_overlap,
        )
        final_metrics = metrics
        last_gemini_payload = gemini_payload
        last_claude_payload = claude_payload

        round_record = {
            "round_index": round_index,
            "gemini": {
                "model": args.gemini_model,
                "parsed_path": str(gemini_parsed_path),
                "log_path": str(gemini_log_path),
            },
            "claude": {
                "model": args.claude_model,
                "parsed_path": str(claude_parsed_path),
                "log_path": str(claude_log_path),
            },
            "consensus_metrics": metrics,
        }
        if local_member_payload is not None:
            round_record["local_member"] = {
                "label": local_member_label,
                "source_path": str(local_member_source_path) if local_member_source_path else "inline",
            }
        round_records.append(round_record)

        peer_from_gemini_path = output_dir / f"corepaper_llm_counsel_peer_from_gemini_{_today_stamp()}_{run_tag}_r{round_index:02d}.json"
        peer_from_claude_path = output_dir / f"corepaper_llm_counsel_peer_from_claude_{_today_stamp()}_{run_tag}_r{round_index:02d}.json"
        peer_context_from_gemini = _build_peer_context(
            source_model=args.gemini_model,
            round_index=round_index,
            critique_payload=gemini_payload,
            consensus_snapshot=metrics,
        )
        peer_context_from_claude = _build_peer_context(
            source_model=args.claude_model,
            round_index=round_index,
            critique_payload=claude_payload,
            consensus_snapshot=metrics,
        )
        _write_json(
            peer_from_gemini_path,
            _build_round_peer_context_payload(
                peer_context=peer_context_from_gemini,
                local_member_label=local_member_label if local_member_payload is not None else None,
                local_member_payload=local_member_payload,
                round_index=round_index,
                consensus_snapshot=metrics,
            ),
        )
        _write_json(
            peer_from_claude_path,
            _build_round_peer_context_payload(
                peer_context=peer_context_from_claude,
                local_member_label=local_member_label if local_member_payload is not None else None,
                local_member_payload=local_member_payload,
                round_index=round_index,
                consensus_snapshot=metrics,
            ),
        )
        peer_for_claude = peer_from_gemini_path
        peer_for_gemini = peer_from_claude_path

        print(
            f"[counsel] round={round_index} reached={metrics.get('consensus_reached')} "
            f"risk_delta={metrics.get('risk_delta')} overlap={metrics.get('topic_overlap'):.3f}"
        )

        if metrics.get("consensus_reached"):
            break

    if not round_records or last_gemini_payload is None or last_claude_payload is None or final_metrics is None:
        print("No successful counsel rounds completed.", file=sys.stderr)
        return 1

    final_payloads: dict[str, dict[str, Any]] = {
        "gemini": last_gemini_payload,
        "claude": last_claude_payload,
    }
    if local_member_payload is not None:
        final_payloads[local_member_label] = local_member_payload

    risk_values = [_risk_score(payload) for payload in final_payloads.values()]
    risk_values = [x for x in risk_values if x is not None]
    final_risk = round(sum(risk_values) / len(risk_values), 3) if risk_values else None
    consensus_reached = bool(final_metrics.get("consensus_reached"))
    if consensus_reached:
        final_verdict = "Consensus achieved"
    else:
        final_verdict = "No full consensus in max rounds"

    consensus_actions = _dedupe_lower(
        [action for payload in final_payloads.values() for action in _extract_actions(payload)]
    )
    consensus_risks = _dedupe_lower(
        [risk for payload in final_payloads.values() for risk in _extract_risks(payload)]
    )

    summary = {
        "mode": "llm_counsel",
        "inspiration": {
            "name": "llm-council",
            "url": COUNCIL_INSPIRATION_URL,
        },
        "provider_invocation_policy": {
            "batch_mode_only": True,
            "details": "Council invokes provider runners only via batch manifests.",
        },
        "consensus_reached": consensus_reached,
        "final_overall_verdict": final_verdict,
        "final_acceptance_risk_score_0_to_10": final_risk,
        "council_seats": list(final_payloads.keys()),
        "consensus_criteria": {
            "max_risk_delta": args.max_risk_delta,
            "min_topic_overlap": args.min_topic_overlap,
            "max_rounds": max_rounds,
        },
        "final_round_metrics": final_metrics,
        "consensus_findings": _merge_consensus_findings_from_sources(final_payloads),
        "consensus_actions": consensus_actions[:12],
        "consensus_residual_risks": consensus_risks[:12],
        "rounds": round_records,
        "source_artifacts": {
            "paper_pdf": str(args.paper_pdf),
            "paper_tex": str(args.paper_tex),
            "plan_md": str(args.plan_md),
        },
        "model_config": {
            "gemini_model": args.gemini_model,
            "gemini_max_tex_chars": args.gemini_max_tex_chars,
            "gemini_max_plan_chars": args.gemini_max_plan_chars,
            "gemini_max_peer_context_chars": args.gemini_max_peer_context_chars,
            "claude_model": args.claude_model,
            "claude_region": args.claude_region,
            "claude_backend": args.claude_backend,
            "claude_schema_mode": args.claude_schema_mode,
            "improvement_directive": args.improvement_directive,
        },
    }
    if local_member_payload is not None:
        summary["local_member"] = {
            "label": local_member_label,
            "source_path": str(local_member_source_path) if local_member_source_path else "inline",
        }

    stamp = _today_stamp()
    parsed_path = output_dir / f"corepaper_llm_counsel_critique_{stamp}_{run_tag}.json"
    summary_path = output_dir / f"corepaper_llm_counsel_critique_{stamp}_{run_tag}.md"
    _write_json(parsed_path, summary)
    _write_markdown_summary(summary_path, consensus=summary)

    print(f"Wrote counsel consensus JSON: {parsed_path}")
    print(f"Wrote counsel summary: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
