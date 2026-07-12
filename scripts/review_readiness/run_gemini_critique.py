#!/usr/bin/env python3
"""Run a Gemini critique pass on current paper and plan artifacts.

This script sends:
1) The compiled paper PDF,
2) The LaTeX manuscript source, and
3) The master research plan,
to Gemini and stores both raw and parsed outputs in Review-Readiness reports.
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_MODEL = "gemini-3.1-pro-preview"
API_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
DEFAULT_HTTP_TIMEOUT_SECONDS = 600
MAX_STRUCTURED_PARSE_ATTEMPTS = 3


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _read_b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def _truncate_with_head_tail(text: str, limit: int) -> str:
    if limit <= 0 or len(text) <= limit:
        return text
    head = max(0, int(limit * 0.6))
    tail = max(0, limit - head)
    return text[:head] + "\n\n... [truncated] ...\n\n" + text[-tail:]


def _extract_json_block(text: str) -> dict:
    fenced = re.search(r"```json\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    if fenced:
        return json.loads(fenced.group(1))

    loose = re.search(r"(\{.*\})", text, flags=re.DOTALL)
    if loose:
        return json.loads(loose.group(1))

    raise ValueError("Could not find JSON object in Gemini response text.")


def _request_gemini(
    *,
    api_key: str,
    model: str,
    paper_pdf_b64: str,
    paper_tex: str,
    plan_md: str,
    peer_context: str,
    max_output_tokens: int,
    http_timeout_seconds: int,
    max_retries: int,
    retry_backoff_seconds: float,
    schema_mode: str,
    thinking_budget: int,
    improvement_directive: str,
) -> dict:
    today = dt.date.today().isoformat()
    deadline = "2026-03-02"
    system = (
        "You are a vigilant IROS reviewer and red-team auditor. "
        "Critique rigor, novelty, external validity, methodology, statistical validity, "
        "theory soundness, writing cohesion, and reproducibility. "
        "Use uncommon reviewer angles in addition to common checks: hidden confounders, "
        "selection leakage, denominator drift, multiplicity mistakes, unfair comparator framing, "
        "claim-evidence mismatch across sections/figures/tables/macros, theorem assumption gaps, "
        "notation inconsistency, visualization accessibility/readability, and reproducibility weak points. "
        "Prioritize desk-reject risk and high-impact findings. Be strict, concrete, and verifiable."
    )

    if schema_mode == "compact":
        schema_prompt = (
            "Deliver a STRICT JSON object (no markdown) with this schema:\n"
            "{\n"
            '  "overall_verdict": string,\n'
            '  "acceptance_risk_score_0_to_10": number,\n'
            '  "strengths": [string],\n'
            '  "top_findings": [\n'
            "    {\n"
            '      "id": string,\n'
            '      "severity": "critical"|"high"|"medium"|"low",\n'
            '      "issue": string,\n'
            '      "fix": string\n'
            "    }\n"
            "  ],\n"
            '  "next_actions": [string],\n'
            '  "residual_risks": [string]\n'
            "}\n\n"
            "Output constraints:\n"
            "- strengths: <= 3 items, each <= 12 words\n"
            "- top_findings: <= 2 items\n"
            "- each top_findings.issue <= 18 words\n"
            "- each top_findings.fix <= 18 words\n"
            "- next_actions: <= 3 items, each <= 12 words\n"
            "- residual_risks: <= 2 items, each <= 12 words\n"
            "- Keep total output under 260 tokens.\n"
            "- End output immediately after the closing JSON brace."
        )
    else:
        schema_prompt = (
            "Deliver a STRICT JSON object (no markdown) with this schema:\n"
            "{\n"
            '  "overall_verdict": string,\n'
            '  "acceptance_risk_score_0_to_10": number,\n'
            '  "strengths": [string],\n'
            '  "critical_findings": [\n'
            "    {\n"
            '      "id": string,\n'
            '      "severity": "critical"|"high"|"medium"|"low",\n'
            '      "issue": string,\n'
            '      "evidence": string,\n'
            '      "impact": string,\n'
            '      "fix": string,\n'
            '      "validation": string\n'
            "    }\n"
            "  ],\n"
            '  "priority_backlog": [\n'
            "    {\n"
            '      "rank": number,\n'
            '      "id": string,\n'
            '      "action": string,\n'
            '      "files": [string],\n'
            '      "effort": "S"|"M"|"L",\n'
            '      "expected_gain": string,\n'
            '      "validation": string\n'
            "    }\n"
            "  ],\n"
            '  "accepted_actions_for_current_repo": [\n'
            "    {\n"
            '      "id": string,\n'
            '      "rationale": string,\n'
            '      "implementation_hint": string\n'
            "    }\n"
            "  ],\n"
            '  "rejected_actions_for_current_repo": [\n'
            "    {\n"
            '      "id": string,\n'
            '      "reason": string\n'
            "    }\n"
            "  ],\n"
            '  "residual_risks": [string]\n'
            "}\n"
        )

    user_prompt = (
        "Critique the attached artifacts for IROS 2026 submission readiness. "
        f"Treat today's date as {today} and the submission deadline as {deadline}.\n\n"
        f"{schema_prompt}\n\n"
        "Review protocol (mandatory):\n"
        "1) Run contradiction-first audit across abstract/introduction/theory/results/discussion/conclusion.\n"
        "2) Cross-check every statistical claim against reported p-values, multiplicity thresholds, and CI signs.\n"
        "3) Verify figure/table claims align with numbers and captions; flag any mismatch or ambiguity.\n"
        "4) Stress-test baseline fairness/parity assumptions and explicitly flag proxy-lane limitations.\n"
        "5) Stress-test theorem/proposition assumptions and proof completeness; flag hand-wavy jumps.\n"
        "6) Score writing cohesion (objective -> method -> evidence -> conclusion) and detect repetition/noise.\n\n"
        "Constraints:\n"
        "- Do not request hardware experiments as mandatory for acceptance; propose software-feasible alternatives.\n"
        "- Highlight notational inconsistencies if found.\n"
        "- Keep fixes executable within a short deadline window.\n"
        "- For each critical/high finding, cite exact evidence anchors (section/table/figure/equation/macro where possible).\n"
    )
    if improvement_directive.strip():
        user_prompt += (
            "\nEnhancement directive (primary objective):\n"
            f"- {improvement_directive.strip()}\n"
            "- Emphasize high-impact, concrete upgrades over generic criticism.\n"
        )

    parts: list[dict[str, Any]] = [
        {"text": user_prompt},
        {"text": "Artifact A: Compiled paper PDF (application/pdf)"},
        {"inlineData": {"mimeType": "application/pdf", "data": paper_pdf_b64}},
        {"text": "Artifact B: LaTeX source (paper/manuscript.tex)"},
        {"text": paper_tex},
        {"text": "Artifact C: Research plan (docs/plan.md)"},
        {"text": plan_md},
    ]
    if peer_context.strip():
        parts.extend(
            [
                {"text": "Artifact D: Peer critique context from counsel loop (JSON text)"},
                {"text": peer_context},
            ]
        )

    body = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [
            {
                "role": "user",
                "parts": parts,
            }
        ],
        "generationConfig": {
            "temperature": 0.15,
            "maxOutputTokens": max_output_tokens,
            "responseMimeType": "application/json",
        },
    }
    if thinking_budget > 0:
        body["generationConfig"]["thinkingConfig"] = {"thinkingBudget": thinking_budget}

    url = API_ENDPOINT.format(model=model, api_key=api_key)
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    attempt = 0
    while True:
        attempt += 1
        try:
            with urllib.request.urlopen(req, timeout=http_timeout_seconds) as resp:
                payload = resp.read().decode("utf-8")
            break
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            transient = exc.code in (429, 503)
            if transient and attempt <= max_retries:
                sleep_seconds = retry_backoff_seconds * (2 ** (attempt - 1))
                print(
                    f"Gemini transient HTTP {exc.code}; retrying in {sleep_seconds:.1f}s "
                    f"(attempt {attempt}/{max_retries}).",
                    file=sys.stderr,
                )
                time.sleep(max(0.1, sleep_seconds))
                continue
            raise RuntimeError(f"Gemini HTTP error {exc.code}: {detail}") from exc

    return json.loads(payload)


def _collect_candidate_text(raw_response: dict) -> str:
    candidates = raw_response.get("candidates", [])
    if not candidates:
        raise ValueError("No candidates in Gemini response.")
    parts = candidates[0].get("content", {}).get("parts", [])
    text_parts = [p.get("text", "") for p in parts if "text" in p]
    if not text_parts:
        raise ValueError("No text parts found in candidate.")
    return "\n".join(text_parts).strip()


def _candidate_finish_reason(raw_response: dict) -> str:
    candidates = raw_response.get("candidates", [])
    if not candidates:
        return ""
    reason = candidates[0].get("finishReason")
    return str(reason) if reason else ""


def _write_markdown_summary(
    output_path: Path,
    *,
    model: str,
    parsed: dict,
    raw_path: Path,
    parsed_path: Path,
) -> None:
    findings = parsed.get("critical_findings", [])
    top = findings[:5]
    lines = [
        f"# Gemini Critique Summary ({dt.date.today().isoformat()})",
        "",
        "## Invocation",
        "",
        f"- Model: `{model}`",
        "- Mode: PDF + LaTeX + plan critique",
        f"- Raw response: `{raw_path}`",
        f"- Parsed factsheet: `{parsed_path}`",
        "",
        "## Verdict",
        "",
        f"- {parsed.get('overall_verdict', 'N/A')}",
        f"- Acceptance risk (0-10): {parsed.get('acceptance_risk_score_0_to_10', 'N/A')}",
        "",
        "## Top Findings",
        "",
    ]
    if not top:
        lines.append("- No critical findings reported.")
    else:
        for item in top:
            fid = item.get("id", "NA")
            sev = item.get("severity", "NA")
            issue = item.get("issue", "")
            fix = item.get("fix", "")
            lines.extend(
                [
                    f"- `{fid}` ({sev}): {issue}",
                    f"  - Fix: {fix}",
                ]
            )
    lines.extend(["", "## Residual Risks", ""])
    risks = parsed.get("residual_risks", [])
    if risks:
        for risk in risks:
            lines.append(f"- {risk}")
    else:
        lines.append("- None listed.")
    output_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def _normalize_tag(tag: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9_.-]+", "-", tag.strip())
    return clean.strip("-._")


def _load_batch_jobs(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        jobs = payload
    elif isinstance(payload, dict) and isinstance(payload.get("jobs"), list):
        jobs = payload["jobs"]
    else:
        raise ValueError("Batch manifest must be a JSON array or object with 'jobs' array.")
    normalized: list[dict[str, Any]] = []
    for i, row in enumerate(jobs, start=1):
        if not isinstance(row, dict):
            raise ValueError(f"Batch job #{i} must be a JSON object.")
        normalized.append(row)
    return normalized


def _run_one(
    *,
    api_key: str,
    paper_pdf: Path,
    paper_tex: Path,
    plan_md: Path,
    output_dir: Path,
    model: str,
    max_output_tokens: int,
    http_timeout_seconds: int,
    max_retries: int,
    retry_backoff_seconds: float,
    schema_mode: str,
    thinking_budget: int,
    improvement_directive: str,
    max_tex_chars: int,
    max_plan_chars: int,
    peer_context: str = "",
    tag: str = "",
) -> int:
    for req in (paper_pdf, paper_tex, plan_md):
        if not req.exists():
            print(f"Missing required file: {req}", file=sys.stderr)
            return 2

    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.date.today().isoformat()
    suffix = ""
    if tag.strip():
        normalized_tag = _normalize_tag(tag)
        if not normalized_tag:
            print(f"Invalid tag for output naming: {tag!r}", file=sys.stderr)
            return 2
        suffix = f"_{normalized_tag}"
    raw_path = output_dir / f"corepaper_gemini_critique_{stamp}{suffix}_raw.json"
    parsed_path = output_dir / f"corepaper_gemini_critique_{stamp}{suffix}.json"
    summary_path = output_dir / f"corepaper_gemini_critique_{stamp}{suffix}.md"
    tex_chars = max(4_000, int(max_tex_chars))
    plan_chars = max(2_000, int(max_plan_chars))
    peer_context_curr = str(peer_context or "")
    parse_exc: Exception | None = None
    parsed: dict[str, Any] | None = None
    raw: dict[str, Any] | None = None

    for attempt in range(1, MAX_STRUCTURED_PARSE_ATTEMPTS + 1):
        paper_tex_text = _truncate_with_head_tail(_read_text(paper_tex), tex_chars)
        plan_md_text = _truncate_with_head_tail(_read_text(plan_md), plan_chars)
        try:
            raw = _request_gemini(
                api_key=api_key,
                model=model,
                paper_pdf_b64=_read_b64(paper_pdf),
                paper_tex=paper_tex_text,
                plan_md=plan_md_text,
                peer_context=peer_context_curr,
                max_output_tokens=max_output_tokens,
                http_timeout_seconds=http_timeout_seconds,
                max_retries=max_retries,
                retry_backoff_seconds=retry_backoff_seconds,
                schema_mode=schema_mode,
                thinking_budget=thinking_budget,
                improvement_directive=improvement_directive,
            )
        except Exception as exc:  # noqa: BLE001
            print(f"Gemini request failed: {exc}", file=sys.stderr)
            return 1

        attempt_raw_path = raw_path
        if attempt > 1:
            attempt_raw_path = output_dir / f"corepaper_gemini_critique_{stamp}{suffix}_raw_retry{attempt-1}.json"
        attempt_raw_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
        if attempt > 1:
            print(
                f"[gemini] wrote retry raw response (attempt {attempt}): {attempt_raw_path}",
                file=sys.stderr,
            )

        try:
            response_text = _collect_candidate_text(raw)
            try:
                parsed = json.loads(response_text)
            except json.JSONDecodeError:
                parsed = _extract_json_block(response_text)
            parse_exc = None
            break
        except Exception as exc:  # noqa: BLE001
            parse_exc = exc
            finish_reason = _candidate_finish_reason(raw)
            if finish_reason == "MAX_TOKENS" and attempt < MAX_STRUCTURED_PARSE_ATTEMPTS:
                tex_chars = max(4_000, int(tex_chars * 0.65))
                plan_chars = max(2_000, int(plan_chars * 0.65))
                if peer_context_curr:
                    peer_context_curr = peer_context_curr[: max(1_000, int(len(peer_context_curr) * 0.5))]
                print(
                    (
                        f"[gemini] structured response truncated at MAX_TOKENS; retrying "
                        f"with smaller prompt budgets (attempt {attempt + 1}/{MAX_STRUCTURED_PARSE_ATTEMPTS}, "
                        f"tex_chars={tex_chars}, plan_chars={plan_chars}, peer_chars={len(peer_context_curr)})."
                    ),
                    file=sys.stderr,
                )
                continue
            break

    if raw is None or parsed is None:
        detail = parse_exc if parse_exc is not None else "unknown parse failure"
        print(f"Failed to parse Gemini structured response: {detail}", file=sys.stderr)
        print(f"Raw response saved to {raw_path}", file=sys.stderr)
        return 1

    raw_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")

    parsed_path.write_text(json.dumps(parsed, indent=2), encoding="utf-8")
    _write_markdown_summary(
        summary_path,
        model=model,
        parsed=parsed,
        raw_path=raw_path,
        parsed_path=parsed_path,
    )
    print(f"Wrote raw response: {raw_path}")
    print(f"Wrote parsed critique: {parsed_path}")
    print(f"Wrote summary: {summary_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--paper-pdf",
        type=Path,
        default=Path("paper/build/manuscript.pdf"),
        help="Path to compiled paper PDF.",
    )
    parser.add_argument(
        "--paper-tex",
        type=Path,
        default=Path("paper/manuscript.tex"),
        help="Path to main LaTeX source.",
    )
    parser.add_argument(
        "--plan-md",
        type=Path,
        default=Path("docs/plan.md"),
        help="Path to research plan markdown.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output/corepaper_reports/review_readiness"),
        help="Directory for critique artifacts.",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("COREPAPER_GEMINI_MODEL_NAME", os.getenv("RM_GEMINI_MODEL_NAME", DEFAULT_MODEL)),
        help="Gemini model ID.",
    )
    parser.add_argument(
        "--max-output-tokens",
        type=int,
        default=8192,
        help="Maximum output tokens.",
    )
    parser.add_argument(
        "--http-timeout-seconds",
        type=int,
        default=int(os.getenv("GEMINI_HTTP_TIMEOUT_SECONDS", DEFAULT_HTTP_TIMEOUT_SECONDS)),
        help="HTTP timeout budget for the Gemini request.",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=int(os.getenv("GEMINI_HTTP_MAX_RETRIES", "4")),
        help="Retry count for transient Gemini HTTP failures (429/503).",
    )
    parser.add_argument(
        "--retry-backoff-seconds",
        type=float,
        default=float(os.getenv("GEMINI_HTTP_RETRY_BACKOFF_SECONDS", "5")),
        help="Base backoff interval (seconds) for transient Gemini retries.",
    )
    parser.add_argument(
        "--schema-mode",
        choices=("full", "compact"),
        default=os.getenv("PIPELINE_GEMINI_SCHEMA_MODE", "compact"),
        help="response schema size; compact is more robust under strict token/time limits",
    )
    parser.add_argument(
        "--thinking-budget",
        type=int,
        default=int(os.getenv("GEMINI_THINKING_BUDGET", "0")),
        help=(
            "Optional Gemini thinking budget. "
            "Values <= 0 omit thinkingConfig and use model defaults."
        ),
    )
    parser.add_argument(
        "--improvement-directive",
        default="",
        help="Optional high-priority instruction to bias output toward substantial paper improvements.",
    )
    parser.add_argument(
        "--max-tex-chars",
        type=int,
        default=120_000,
        help="Max LaTeX source chars included in prompt (head+tail truncation).",
    )
    parser.add_argument(
        "--max-plan-chars",
        type=int,
        default=120_000,
        help="Max plan markdown chars included in prompt (head+tail truncation).",
    )
    parser.add_argument(
        "--peer-context-json",
        type=Path,
        default=None,
        help="Optional JSON file with peer critique context for counsel roundtrips.",
    )
    parser.add_argument(
        "--max-peer-context-chars",
        type=int,
        default=40_000,
        help="Optional truncation budget for peer context text.",
    )
    parser.add_argument(
        "--tag",
        default="",
        help="Optional tag appended to output artifact filenames.",
    )
    parser.add_argument(
        "--batch-manifest",
        type=Path,
        default=None,
        help=(
            "JSON manifest (array or {'jobs':[...]}). Each job may override any CLI input. "
            "If omitted, a single default batch job is built from CLI flags."
        ),
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop batch execution on first failed job.",
    )
    args = parser.parse_args()

    api_key = os.getenv("COREPAPER_GEMINI_API_KEY", "").strip()
    if not api_key:
        print("Missing COREPAPER_GEMINI_API_KEY in environment.", file=sys.stderr)
        return 2

    if args.batch_manifest is None:
        jobs: list[dict[str, Any]] = [
            {
                "paper_pdf": str(args.paper_pdf),
                "paper_tex": str(args.paper_tex),
                "plan_md": str(args.plan_md),
                "output_dir": str(args.output_dir),
                "model": args.model,
                "max_output_tokens": args.max_output_tokens,
                "http_timeout_seconds": args.http_timeout_seconds,
                "max_retries": args.max_retries,
                "retry_backoff_seconds": args.retry_backoff_seconds,
                "schema_mode": args.schema_mode,
                "thinking_budget": args.thinking_budget,
                "improvement_directive": args.improvement_directive,
                "max_tex_chars": args.max_tex_chars,
                "max_plan_chars": args.max_plan_chars,
                "peer_context_json": str(args.peer_context_json) if args.peer_context_json else "",
                "max_peer_context_chars": args.max_peer_context_chars,
                "tag": args.tag,
            }
        ]
    else:
        if not args.batch_manifest.exists():
            print(f"Missing batch manifest: {args.batch_manifest}", file=sys.stderr)
            return 2
        try:
            jobs = _load_batch_jobs(args.batch_manifest)
        except Exception as exc:  # noqa: BLE001
            print(f"Invalid batch manifest: {exc}", file=sys.stderr)
            return 2
        if not jobs:
            print("Batch manifest has no jobs.", file=sys.stderr)
            return 2

    failures = 0
    for idx, job in enumerate(jobs, start=1):
        paper_pdf = Path(str(job.get("paper_pdf", args.paper_pdf)))
        paper_tex = Path(str(job.get("paper_tex", args.paper_tex)))
        plan_md = Path(str(job.get("plan_md", args.plan_md)))
        output_dir = Path(str(job.get("output_dir", args.output_dir)))
        model = str(job.get("model", args.model))
        max_output_tokens = int(job.get("max_output_tokens", args.max_output_tokens))
        http_timeout_seconds = int(job.get("http_timeout_seconds", args.http_timeout_seconds))
        max_retries = int(job.get("max_retries", args.max_retries))
        retry_backoff_seconds = float(job.get("retry_backoff_seconds", args.retry_backoff_seconds))
        schema_mode = str(job.get("schema_mode", args.schema_mode))
        thinking_budget = int(job.get("thinking_budget", args.thinking_budget))
        improvement_directive = str(job.get("improvement_directive", args.improvement_directive))
        max_tex_chars = int(job.get("max_tex_chars", args.max_tex_chars))
        max_plan_chars = int(job.get("max_plan_chars", args.max_plan_chars))
        max_peer_context_chars = int(job.get("max_peer_context_chars", args.max_peer_context_chars))
        peer_context_path_raw = str(job.get("peer_context_json", "")).strip()
        peer_context = ""
        if peer_context_path_raw:
            peer_context_path = Path(peer_context_path_raw)
            if not peer_context_path.exists():
                print(f"Missing peer context JSON: {peer_context_path}", file=sys.stderr)
                code = 2
                failures += 1
                print(f"[batch] job {idx} failed with code={code}", file=sys.stderr)
                if args.fail_fast:
                    return code
                continue
            peer_context = _read_text(peer_context_path)
            if max_peer_context_chars > 0:
                peer_context = peer_context[:max_peer_context_chars]
        tag = str(job.get("tag", f"job{idx:02d}"))
        print(f"[batch] job {idx}/{len(jobs)} model={model} tag={tag}", flush=True)
        code = _run_one(
            api_key=api_key,
            paper_pdf=paper_pdf,
            paper_tex=paper_tex,
            plan_md=plan_md,
            output_dir=output_dir,
            model=model,
            max_output_tokens=max_output_tokens,
            http_timeout_seconds=http_timeout_seconds,
            max_retries=max_retries,
            retry_backoff_seconds=retry_backoff_seconds,
            schema_mode=schema_mode,
            thinking_budget=thinking_budget,
            improvement_directive=improvement_directive,
            max_tex_chars=max_tex_chars,
            max_plan_chars=max_plan_chars,
            peer_context=peer_context,
            tag=tag,
        )
        if code != 0:
            failures += 1
            print(f"[batch] job {idx} failed with code={code}", file=sys.stderr)
            if args.fail_fast:
                return code
    if failures:
        print(f"[batch] completed with {failures} failed job(s)", file=sys.stderr)
        return 1
    print(f"[batch] completed successfully: {len(jobs)} job(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
