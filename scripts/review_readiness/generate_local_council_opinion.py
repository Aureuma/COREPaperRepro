#!/usr/bin/env python3
"""Generate a deterministic local council opinion for LLM counsel rounds.

This script is the local "Codex seat" in the counsel loop. It does not call
external APIs; it scores manuscript rigor with fixed heuristics and emits a
compact JSON critique payload compatible with counsel consensus aggregation.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path
from typing import Any


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _count(pattern: str, text: str) -> int:
    return len(re.findall(pattern, text, flags=re.IGNORECASE))


def _has_scope_guard(text_lower: str) -> bool:
    return (
        "simulation-only" in text_lower
        or "benchmark/simulation scoped" in text_lower
        or "benchmark-scoped" in text_lower
    )


def _severity_rank(severity: str) -> int:
    mapping = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    return mapping.get(severity.lower(), 4)


def _extract_float_macro(macros_text: str, macro_name: str) -> float | None:
    pattern = rf"\\providecommand\{{\\{re.escape(macro_name)}\}}\{{([^}}]+)\}}"
    match = re.search(pattern, macros_text)
    if not match:
        return None
    raw = match.group(1).strip().replace("+", "")
    if raw.startswith("<"):
        raw = raw[1:].strip()
    try:
        return float(raw)
    except ValueError:
        return None


def _build_findings(
    *,
    paper_text: str,
    plan_text: str,
    parity_report: Path,
    macros_text: str = "",
) -> tuple[list[dict[str, str]], float]:
    text_lower = paper_text.lower()
    plan_lower = plan_text.lower()

    floor_terms = _count(r"\bfloor\b|\bcvar\b|\bworst", text_lower)
    mean_terms = _count(r"\bmean\b", text_lower)
    theorem_count = _count(r"\\begin\{theorem\}", paper_text)
    proposition_count = _count(r"\\begin\{proposition\}", paper_text)
    proof_count = _count(r"proof\.", paper_text)
    subsection_count = _count(r"\\subsection\{", paper_text)
    has_scope_guard = _has_scope_guard(text_lower)
    has_plan_status_table = "status" in plan_lower and "| id |" in plan_lower
    has_proxy_rounding_caveat = "round to 0.0000" in text_lower or "4-decimal display precision" in text_lower

    p_mean_n30 = _extract_float_macro(macros_text, "CoreMetaSeedExpLatencyNThirtyP")
    p_cvar_n30 = _extract_float_macro(macros_text, "CoreMetaSeedExpLatencyNThirtyPCvar")
    p_holm_adapt_mean = _extract_float_macro(macros_text, "CoreMetaDeepFamilyHolmAdaptMeanP")
    p_holm_adapt_cvar = _extract_float_macro(macros_text, "CoreMetaDeepFamilyHolmAdaptCvarP")
    p_holm_latency_mean = _extract_float_macro(macros_text, "CoreMetaDeepFamilyHolmLatencyMeanP")
    p_holm_latency_cvar = _extract_float_macro(macros_text, "CoreMetaDeepFamilyHolmLatencyCvarP")
    latency_worst_delta = _extract_float_macro(macros_text, "CoreMetaSeedExpLatencyNThirtyWorstDelta")

    findings: list[dict[str, str]] = []
    risk = 4.2

    if subsection_count > 0:
        findings.append(
            {
                "id": "CDX-01",
                "severity": "high",
                "issue": "Paper uses subsection headers despite no-subsection policy.",
                "fix": "Flatten subsection blocks into paragraph-level bold lead-ins.",
            }
        )
        risk += 1.0

    if mean_terms > max(1, int(floor_terms * 1.8)):
        findings.append(
            {
                "id": "CDX-02",
                "severity": "high",
                "issue": "Mean framing still dominates floor framing in key sections.",
                "fix": "Lead each result paragraph with CVaR/worst-seed and keep mean secondary.",
            }
        )
        risk += 0.9

    theorem_like_count = theorem_count + proposition_count
    if theorem_like_count == 0:
        findings.append(
            {
                "id": "CDX-03",
                "severity": "high",
                "issue": "No explicit proposition/theorem guarantees are present in the theory section.",
                "fix": "Add assumption-scoped floor-oriented proposition/theorem statements with concise proofs.",
            }
        )
        risk += 1.1
    elif proof_count < theorem_like_count:
        findings.append(
            {
                "id": "CDX-04",
                "severity": "medium",
                "issue": "At least one proposition/theorem lacks an explicit proof block.",
                "fix": "Attach concise proofs or label unproved statements as conjectural.",
            }
        )
        risk += 0.6

    if not has_scope_guard:
        findings.append(
            {
                "id": "CDX-05",
                "severity": "high",
                "issue": "Scope limits are not explicit enough for simulation-only evidence.",
                "fix": "State benchmark/simulation scope boundaries in abstract, results, and conclusion.",
            }
        )
        risk += 0.8

    if not parity_report.exists():
        findings.append(
            {
                "id": "CDX-06",
                "severity": "medium",
                "issue": "Official-code parity artifact for library lane is missing.",
                "fix": "Run official parity audit and cite report path in paper evidence sentence.",
            }
        )
        risk += 0.5

    if not has_plan_status_table:
        findings.append(
            {
                "id": "CDX-07",
                "severity": "medium",
                "issue": "Plan lacks a clear status ledger for critique-driven actions.",
                "fix": "Track critique -> plan -> implementation items with status and commit linkage.",
            }
        )
        risk += 0.4

    if (
        p_holm_adapt_mean is not None
        and p_holm_adapt_cvar is not None
        and "significant versus \\texttt{adaptmanip}" in text_lower
        and p_holm_adapt_mean >= 0.05
        and p_holm_adapt_cvar >= 0.05
    ):
        findings.append(
            {
                "id": "CDX-08",
                "severity": "critical",
                "issue": "Deep-N text claims Holm significance versus adaptmanip but adjusted p-values exceed 0.05.",
                "fix": "Use exact 4-test Holm step-down values and keep adaptmanip deep effects directional/inconclusive.",
            }
        )
        risk += 1.4

    if (
        p_holm_adapt_mean is not None
        and p_holm_adapt_cvar is not None
        and (
            "both mean and cvar are not statistically separated" in text_lower
            or "not significantly different in mean/cvar" in text_lower
        )
        and (p_holm_adapt_mean < 0.05 or p_holm_adapt_cvar < 0.05)
    ):
        findings.append(
            {
                "id": "CDX-09",
                "severity": "critical",
                "issue": "Deep-N text claims full non-significance while at least one Holm-adjusted adaptmanip metric is significant.",
                "fix": "Split mean and CVaR statements and align wording to adjusted p-values.",
            }
        )
        risk += 1.4

    if (
        latency_worst_delta is not None
        and abs(latency_worst_delta) > 1e-9
        and "tied on worst-seed" in text_lower
    ):
        findings.append(
            {
                "id": "CDX-11",
                "severity": "critical",
                "issue": "Abstract claims worst-seed tie while deep latency worst-seed delta is non-zero.",
                "fix": "Report the signed worst-seed delta directly and avoid tie wording.",
            }
        )
        risk += 1.0

    if (
        _extract_float_macro(macros_text, "CoreLatencyProxyPaperGapMean") == 0.0
        and _extract_float_macro(macros_text, "CoreLatencyProxyPaperGapWorst") == 0.0
        and _extract_float_macro(macros_text, "CoreLatencyProxyPaperGapCvar") == 0.0
        and not has_proxy_rounding_caveat
    ):
        findings.append(
            {
                "id": "CDX-10",
                "severity": "high",
                "issue": "Proxy target-verification shows all-zero gaps without rounding/provenance caveat.",
                "fix": "Add same-scorer rounding caveat and state this does not prove full official parity.",
            }
        )
        risk += 0.8

    if not findings:
        findings.append(
            {
                "id": "CDX-OK",
                "severity": "low",
                "issue": "No blocking issues detected by local rigor heuristics.",
                "fix": "Preserve current floor-first framing and reproducibility discipline.",
            }
        )
        risk = 2.8

    findings.sort(key=lambda row: (_severity_rank(row["severity"]), row["id"]))
    return findings, max(0.0, min(10.0, round(risk, 2)))


def _derive_verdict(risk: float) -> str:
    if risk <= 3.5:
        return "Strong submission"
    if risk <= 5.0:
        return "Near-ready"
    if risk <= 7.0:
        return "High risk"
    return "Reject risk"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper-tex", type=Path, default=Path("paper/manuscript.tex"))
    parser.add_argument("--plan-md", type=Path, default=Path("docs/plan.md"))
    parser.add_argument(
        "--parity-report-json",
        type=Path,
        default=Path("output/corepaper_reports/ws5/library_parity_official.json"),
        help="Optional parity report artifact used by local consistency checks.",
    )
    parser.add_argument(
        "--macros-tex",
        type=Path,
        default=Path("paper/generated/results_macros.tex"),
        help="Optional macros file used for local claim-vs-number consistency checks.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=Path("output/corepaper_reports/review_readiness/corepaper_local_council_opinion_latest.json"),
    )
    parser.add_argument(
        "--label",
        default="codex",
        help="Seat label stored in metadata only.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    for required in (args.paper_tex, args.plan_md):
        if not required.exists():
            raise SystemExit(f"Missing required file: {required}")

    paper_text = _read_text(args.paper_tex)
    plan_text = _read_text(args.plan_md)
    macros_text = _read_text(args.macros_tex) if args.macros_tex.exists() else ""
    findings, risk = _build_findings(
        paper_text=paper_text,
        plan_text=plan_text,
        parity_report=args.parity_report_json,
        macros_text=macros_text,
    )

    strengths: list[str] = []
    text_lower = paper_text.lower()
    if _count(r"\bcvar\b|\bworst", text_lower) >= 8:
        strengths.append("Floor metrics are consistently reported.")
    if _count(r"matched-seed|matched seed", text_lower) >= 3:
        strengths.append("Matched-seed protocol improves comparison rigor.")
    if _has_scope_guard(text_lower):
        strengths.append("Scope boundaries are explicitly stated.")
    if not strengths:
        strengths = ["Core method and evaluation pipeline are clearly described."]

    top_findings = findings[:2]
    next_actions = [row["fix"] for row in top_findings]
    residual_risks = [
        row["issue"]
        for row in findings
        if row.get("severity", "").lower() in {"critical", "high", "medium"}
    ][:3]

    payload: dict[str, Any] = {
        "source": "local_council_codex",
        "label": args.label,
        "generated_at_utc": dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "overall_verdict": _derive_verdict(risk),
        "acceptance_risk_score_0_to_10": risk,
        "strengths": strengths[:3],
        "top_findings": top_findings,
        "critical_findings": findings[:4],
        "next_actions": next_actions[:3],
        "residual_risks": residual_risks,
    }

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote local council opinion: {args.output_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
