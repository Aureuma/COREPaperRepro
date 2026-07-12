#!/usr/bin/env python3
"""Run a Bedrock Claude critique pass on current paper and plan artifacts.

This script mirrors the Gemini critique flow, but uses SI's AWS Bedrock
integration (`si aws bedrock runtime converse`) with Anthropic Claude models.
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


DEFAULT_MODEL = "us.anthropic.claude-opus-4-6-v1"
ALLOWED_MODELS = {
    "anthropic.claude-sonnet-4-6",
    "anthropic.claude-opus-4-6-v1",
}


def _is_allowed_model(model_id: str) -> bool:
    model_id = model_id.strip().lower()
    if model_id in ALLOWED_MODELS:
        return True
    return "claude-sonnet-4-6" in model_id or "claude-opus-4-6" in model_id


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _corepaper_aws_credentials() -> dict[str, str]:
    access_key = os.getenv("COREPAPER_AWS_ACCESS_KEY_ID", "").strip()
    secret_key = os.getenv("COREPAPER_AWS_SECRET_ACCESS_KEY", "").strip()
    session_token = os.getenv("COREPAPER_AWS_SESSION_TOKEN", "").strip()
    if bool(access_key) != bool(secret_key):
        raise RuntimeError(
            "COREPAPER_AWS_ACCESS_KEY_ID and COREPAPER_AWS_SECRET_ACCESS_KEY must be set together."
        )
    creds: dict[str, str] = {}
    if access_key and secret_key:
        creds["aws_access_key_id"] = access_key
        creds["aws_secret_access_key"] = secret_key
        if session_token:
            creds["aws_session_token"] = session_token
    return creds


def _truncate_with_head_tail(text: str, max_chars: int) -> str:
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    head = int(max_chars * 0.7)
    tail = max_chars - head
    return (
        text[:head]
        + "\n\n[... TRUNCATED FOR TOKEN BUDGET ...]\n\n"
        + text[-tail:]
    )


def _fallback_pdf_text_dump(pdf_path: Path) -> tuple[str, str]:
    fallback = (
        pdf_path.parent.parent / "output" / "corepaper_reports" / "review_readiness" / "pdf_text_extract_latest.txt"
    )
    if fallback.exists():
        text = fallback.read_text(encoding="utf-8", errors="replace")
        if text.strip():
            return text, f"PDF text loaded from fallback dump: {fallback}"
    return "", ""


def _extract_pdf_text_pypdf(pdf_path: Path) -> tuple[str, str]:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception:
        return "", ""

    try:
        reader = PdfReader(str(pdf_path))
        chunks: list[str] = []
        for page in reader.pages:
            chunks.append(page.extract_text() or "")
        text = "\n\n".join(chunks).strip()
    except Exception:
        return "", ""

    if text:
        return text, "PDF text extracted via pypdf fallback."
    return "", ""


def _extract_pdf_text(pdf_path: Path) -> tuple[str, str]:
    pdftotext = subprocess.run(
        ["bash", "-lc", "command -v pdftotext"],
        capture_output=True,
        text=True,
        check=False,
    )
    if pdftotext.returncode != 0 or not pdftotext.stdout.strip():
        text, note = _extract_pdf_text_pypdf(pdf_path)
        if text:
            return text, note
        text, note = _fallback_pdf_text_dump(pdf_path)
        if text:
            return text, note
        return "", "pdftotext not available and no fallback text extraction succeeded."

    proc = subprocess.run(
        [pdftotext.stdout.strip(), "-layout", str(pdf_path), "-"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        text, note = _extract_pdf_text_pypdf(pdf_path)
        if text:
            return text, note
        text, note = _fallback_pdf_text_dump(pdf_path)
        if text:
            return text, note
        return "", f"pdftotext failed (exit {proc.returncode}); no fallback extraction succeeded."
    return proc.stdout, "PDF text extracted via pdftotext."


def _extract_json_block(text: str) -> dict[str, Any]:
    fenced = re.search(r"```json\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    if fenced:
        return json.loads(fenced.group(1))
    loose = re.search(r"(\{.*\})", text, flags=re.DOTALL)
    if loose:
        return json.loads(loose.group(1))
    raise ValueError("Could not find JSON object in model response text.")


def _collect_response_text(raw_response: dict[str, Any]) -> str:
    data = raw_response.get("data", raw_response) or {}
    content = (
        data.get("output", {})
        .get("message", {})
        .get("content", [])
    )
    chunks = [entry.get("text", "") for entry in content if isinstance(entry, dict) and "text" in entry]
    if not chunks:
        raise ValueError("No text content found in Bedrock response.")
    return "\n".join(chunks).strip()


def _request_bedrock_via_si(
    *,
    si_bin: str,
    model: str,
    region: str,
    body_path: Path,
) -> dict[str, Any]:
    cmd = [
        si_bin,
        "aws",
        "bedrock",
        "runtime",
        "converse",
        "--model-id",
        model,
        "--body-file",
        str(body_path),
        "--region",
        region,
        "--json",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    stdout = (proc.stdout or "").strip()
    stderr = (proc.stderr or "").strip()
    if not stdout:
        raise RuntimeError(f"Empty Bedrock response. stderr={stderr}")
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Bedrock response was not JSON. "
            f"exit={proc.returncode}; stdout={stdout[:1200]}; stderr={stderr[:1200]}"
        ) from exc

    status_code = int(payload.get("status_code", 0) or 0)
    if status_code >= 400:
        raise RuntimeError(
            f"Bedrock HTTP error status_code={status_code}; "
            f"body={payload.get('body', '')[:1200]}"
        )
    payload.setdefault("backend", "si")
    return payload


def _request_bedrock_via_boto3(
    *,
    model: str,
    region: str,
    request_body: dict[str, Any],
) -> dict[str, Any]:
    try:
        import boto3  # type: ignore
        from botocore.exceptions import BotoCoreError, ClientError  # type: ignore
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            "boto3 is required for --backend boto3/auto fallback. "
            "Install with: uv add boto3"
        ) from exc

    try:
        client_kwargs: dict[str, Any] = {"region_name": region}
        client_kwargs.update(_corepaper_aws_credentials())
        client = boto3.client("bedrock-runtime", **client_kwargs)
        response = client.converse(
            modelId=model,
            system=request_body.get("system", []),
            messages=request_body.get("messages", []),
            inferenceConfig=request_body.get("inferenceConfig", {}),
        )
    except (BotoCoreError, ClientError) as exc:
        raise RuntimeError(f"boto3 Bedrock converse failed: {exc}") from exc

    return {"backend": "boto3", "data": response}


def _write_markdown_summary(
    output_path: Path,
    *,
    model: str,
    region: str,
    backend: str,
    parsed: dict[str, Any],
    raw_path: Path,
    parsed_path: Path,
) -> None:
    findings = parsed.get("critical_findings", parsed.get("top_findings", []))
    top = findings[:5] if isinstance(findings, list) else []
    lines = [
        f"# Bedrock Claude Critique Summary ({dt.date.today().isoformat()})",
        "",
        "## Invocation",
        "",
        f"- Model: `{model}`",
        f"- Region: `{region}`",
        f"- Backend: `{backend}`",
        "- Mode: PDF-text + LaTeX + plan critique",
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
            lines.append(f"- `{fid}` ({sev}): {issue}")
            lines.append(f"  - Fix: {fix}")
    lines.extend(["", "## Residual Risks", ""])
    risks = parsed.get("residual_risks", [])
    if isinstance(risks, list) and risks:
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
    paper_pdf: Path,
    paper_tex_path: Path,
    plan_md_path: Path,
    output_dir: Path,
    si_bin: str,
    model: str,
    region: str,
    backend: str,
    max_output_tokens: int,
    max_tex_chars: int,
    max_plan_chars: int,
    max_pdf_chars: int,
    peer_context: str,
    schema_mode: str,
    improvement_directive: str,
    tag: str = "",
) -> int:
    if not _is_allowed_model(model):
        allowed = ", ".join(sorted(ALLOWED_MODELS))
        print(
            f"Invalid --model '{model}'. Allowed model IDs must be Opus/Sonnet 4.6. "
            f"Direct IDs: {allowed}",
            file=sys.stderr,
        )
        return 2

    if backend not in ("auto", "si", "boto3"):
        print(f"Invalid --backend '{backend}'. Must be one of: auto, si, boto3.", file=sys.stderr)
        return 2

    if schema_mode not in ("full", "compact"):
        print(f"Invalid --schema-mode '{schema_mode}'. Must be one of: full, compact.", file=sys.stderr)
        return 2

    for req in (paper_pdf, paper_tex_path, plan_md_path):
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
    request_path = output_dir / f"corepaper_bedrock_claude_critique_{stamp}{suffix}_request.json"
    raw_path = output_dir / f"corepaper_bedrock_claude_critique_{stamp}{suffix}_raw.json"
    parsed_path = output_dir / f"corepaper_bedrock_claude_critique_{stamp}{suffix}.json"
    summary_path = output_dir / f"corepaper_bedrock_claude_critique_{stamp}{suffix}.md"

    paper_tex = _truncate_with_head_tail(_read_text(paper_tex_path), max_tex_chars)
    plan_md = _truncate_with_head_tail(_read_text(plan_md_path), max_plan_chars)
    pdf_text, pdf_note = _extract_pdf_text(paper_pdf)
    pdf_text = _truncate_with_head_tail(pdf_text, max_pdf_chars)

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
            "Return STRICT JSON only (no markdown) with schema:\n"
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
            "}\n"
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
            "Return STRICT JSON only (no markdown) with schema:\n"
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
        "Critique the artifacts for IROS 2026 submission readiness. "
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
        "- Do not require hardware experiments as mandatory; provide software-feasible alternatives.\n"
        "- Flag notational inconsistencies if found.\n"
        "- Keep fixes executable within a short deadline window.\n\n"
        "- For each critical/high finding, cite exact evidence anchors (section/table/figure/equation/macro where possible).\n\n"
        f"Artifact A (PDF text note): {pdf_note}\n"
        "Artifact A (PDF extracted text):\n"
        f"{pdf_text}\n\n"
        "Artifact B (LaTeX source, paper/manuscript.tex):\n"
        f"{paper_tex}\n\n"
        "Artifact C (research plan, docs/plan.md):\n"
        f"{plan_md}\n"
    )
    if improvement_directive.strip():
        user_prompt += (
            "\nEnhancement directive (primary objective):\n"
            f"- {improvement_directive.strip()}\n"
            "- Prioritize concrete, high-impact upgrades over generic criticism.\n"
        )
    if peer_context.strip():
        user_prompt += (
            "\nArtifact D (peer critique context from counsel loop, JSON text):\n"
            f"{peer_context}\n"
        )

    request_body = {
        "system": [{"text": system}],
        "messages": [
            {
                "role": "user",
                "content": [{"text": user_prompt}],
            }
        ],
        "inferenceConfig": {
            "temperature": 0.15,
            "maxTokens": max_output_tokens,
        },
    }
    request_path.write_text(json.dumps(request_body, indent=2), encoding="utf-8")

    raw: dict[str, Any] | None = None
    errors: list[str] = []
    used_backend = ""

    if backend in ("auto", "si"):
        try:
            raw = _request_bedrock_via_si(
                si_bin=si_bin,
                model=model,
                region=region,
                body_path=request_path,
            )
            used_backend = "si"
        except Exception as exc:  # noqa: BLE001
            message = str(exc)
            if "on-demand throughput isn’t supported" in message or "on-demand throughput isn't supported" in message:
                message += (
                    "\nHint: this model requires an inference profile ID/ARN. "
                    "Pass that profile ID via --model (it must still be Opus/Sonnet 4.6)."
                )
            errors.append(f"SI backend failed: {message}")

    if raw is None and backend in ("auto", "boto3"):
        try:
            raw = _request_bedrock_via_boto3(
                model=model,
                region=region,
                request_body=request_body,
            )
            used_backend = "boto3"
        except Exception as exc:  # noqa: BLE001
            errors.append(f"boto3 backend failed: {exc}")

    if raw is None:
        print("Bedrock request failed via all enabled backends:", file=sys.stderr)
        for err in errors:
            print(f"- {err}", file=sys.stderr)
        return 1

    raw_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")

    try:
        response_text = _collect_response_text(raw)
        try:
            parsed = json.loads(response_text)
        except json.JSONDecodeError:
            parsed = _extract_json_block(response_text)
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to parse Bedrock structured response: {exc}", file=sys.stderr)
        print(f"Raw response saved to {raw_path}", file=sys.stderr)
        return 1

    parsed_path.write_text(json.dumps(parsed, indent=2), encoding="utf-8")
    _write_markdown_summary(
        summary_path,
        model=model,
        region=region,
        backend=used_backend or str(raw.get("backend", "unknown")),
        parsed=parsed,
        raw_path=raw_path,
        parsed_path=parsed_path,
    )

    print(f"Wrote request payload: {request_path}")
    print(f"Wrote raw response: {raw_path}")
    print(f"Wrote parsed critique: {parsed_path}")
    print(f"Wrote summary: {summary_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper-pdf", type=Path, default=Path("paper/build/manuscript.pdf"))
    parser.add_argument("--paper-tex", type=Path, default=Path("paper/manuscript.tex"))
    parser.add_argument("--plan-md", type=Path, default=Path("docs/plan.md"))
    parser.add_argument("--output-dir", type=Path, default=Path("output/corepaper_reports/review_readiness"))
    parser.add_argument("--si-bin", default=os.getenv("SI_BIN", "si"))
    parser.add_argument(
        "--model",
        default=os.getenv("COREPAPER_BEDROCK_MODEL_ID", os.getenv("BEDROCK_MODEL_ID", DEFAULT_MODEL)),
    )
    parser.add_argument("--region", default=os.getenv("COREPAPER_AWS_DEFAULT_REGION", "us-east-1"))
    parser.add_argument(
        "--backend",
        choices=("auto", "si", "boto3"),
        default="auto",
        help="Invocation backend: SI CLI first with optional boto3 fallback.",
    )
    parser.add_argument("--max-output-tokens", type=int, default=4096)
    parser.add_argument("--max-tex-chars", type=int, default=120_000)
    parser.add_argument("--max-plan-chars", type=int, default=120_000)
    parser.add_argument("--max-pdf-chars", type=int, default=80_000)
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
        "--schema-mode",
        choices=("full", "compact"),
        default="full",
        help="response schema size; compact is more robust under strict token/time limits",
    )
    parser.add_argument(
        "--improvement-directive",
        default="",
        help="Optional high-priority instruction to bias output toward substantial paper improvements.",
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

    if args.batch_manifest is None:
        jobs: list[dict[str, Any]] = [
            {
                "paper_pdf": str(args.paper_pdf),
                "paper_tex": str(args.paper_tex),
                "plan_md": str(args.plan_md),
                "output_dir": str(args.output_dir),
                "si_bin": args.si_bin,
                "model": args.model,
                "region": args.region,
                "backend": args.backend,
                "max_output_tokens": args.max_output_tokens,
                "max_tex_chars": args.max_tex_chars,
                "max_plan_chars": args.max_plan_chars,
                "max_pdf_chars": args.max_pdf_chars,
                "peer_context_json": str(args.peer_context_json) if args.peer_context_json else "",
                "max_peer_context_chars": args.max_peer_context_chars,
                "schema_mode": args.schema_mode,
                "improvement_directive": args.improvement_directive,
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
        try:
            paper_pdf = Path(str(job.get("paper_pdf", args.paper_pdf)))
            paper_tex = Path(str(job.get("paper_tex", args.paper_tex)))
            plan_md = Path(str(job.get("plan_md", args.plan_md)))
            output_dir = Path(str(job.get("output_dir", args.output_dir)))
            si_bin = str(job.get("si_bin", args.si_bin))
            model = str(job.get("model", args.model))
            region = str(job.get("region", args.region))
            backend = str(job.get("backend", args.backend))
            max_output_tokens = int(job.get("max_output_tokens", args.max_output_tokens))
            max_tex_chars = int(job.get("max_tex_chars", args.max_tex_chars))
            max_plan_chars = int(job.get("max_plan_chars", args.max_plan_chars))
            max_pdf_chars = int(job.get("max_pdf_chars", args.max_pdf_chars))
            max_peer_context_chars = int(job.get("max_peer_context_chars", args.max_peer_context_chars))
            peer_context_path_raw = str(job.get("peer_context_json", "")).strip()
            peer_context = ""
            if peer_context_path_raw:
                peer_context_path = Path(peer_context_path_raw)
                if not peer_context_path.exists():
                    raise ValueError(f"Missing peer context JSON: {peer_context_path}")
                peer_context = _read_text(peer_context_path)
                if max_peer_context_chars > 0:
                    peer_context = peer_context[:max_peer_context_chars]
            schema_mode = str(job.get("schema_mode", args.schema_mode))
            improvement_directive = str(job.get("improvement_directive", args.improvement_directive))
            tag = str(job.get("tag", f"job{idx:02d}"))
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"[batch] job {idx} has invalid config: {exc}", file=sys.stderr)
            if args.fail_fast:
                return 2
            continue

        print(
            f"[batch] job {idx}/{len(jobs)} model={model} region={region} backend={backend} tag={tag}",
            flush=True,
        )
        code = _run_one(
            paper_pdf=paper_pdf,
            paper_tex_path=paper_tex,
            plan_md_path=plan_md,
            output_dir=output_dir,
            si_bin=si_bin,
            model=model,
            region=region,
            backend=backend,
            max_output_tokens=max_output_tokens,
            max_tex_chars=max_tex_chars,
            max_plan_chars=max_plan_chars,
            max_pdf_chars=max_pdf_chars,
            peer_context=peer_context,
            schema_mode=schema_mode,
            improvement_directive=improvement_directive,
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
