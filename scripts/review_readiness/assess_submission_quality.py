#!/usr/bin/env python3
"""Compute a structured paper-quality assessment from current evidence artifacts."""

from __future__ import annotations

import argparse
import json
import pathlib
from datetime import datetime, timezone
from typing import Dict, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--metaworld-json",
        default="output/corepaper_reports/ws3/metaworld_slice_results.json",
    )
    parser.add_argument(
        "--external-n14-summary-json",
        default="output/corepaper_reports/ws3/corepaper_external_n14_summary.json",
    )
    parser.add_argument(
        "--external-n14-effects-json",
        default="output/corepaper_reports/ws5/corepaper_external_n14_statistical_effects.json",
    )
    parser.add_argument(
        "--reliability-n14-json",
        default="output/corepaper_reports/ws5/corepaper_reliability_floor_n14.json",
    )
    parser.add_argument(
        "--uncertainty-json",
        default="output/corepaper_reports/ws5/uncertainty_dominance.json",
    )
    parser.add_argument(
        "--output-json",
        default="output/corepaper_reports/review_readiness/corepaper_quality_assessment_latest.json",
    )
    parser.add_argument(
        "--output-md",
        default="output/corepaper_reports/review_readiness/corepaper_quality_assessment_latest.md",
    )
    return parser.parse_args()


def load_json(path: pathlib.Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def clamp_score(value: float) -> float:
    return max(0.0, min(10.0, value))


def score_to_priority(score: float) -> str:
    if score < 5.0:
        return "P0"
    if score < 7.0:
        return "P1"
    if score < 8.5:
        return "P2"
    return "P3"


def main() -> int:
    args = parse_args()

    metaworld = load_json(pathlib.Path(args.metaworld_json))
    ext_n14_summary = load_json(pathlib.Path(args.external_n14_summary_json))
    ext_n14_effects = load_json(pathlib.Path(args.external_n14_effects_json))
    rel_n14 = load_json(pathlib.Path(args.reliability_n14_json))
    uncertainty = load_json(pathlib.Path(args.uncertainty_json))

    shifted = metaworld["summary"]["shifted"]
    shifted_gap_ext2 = float(shifted["method"]["mean_success"] - shifted["ext2"]["mean_success"])

    n14_rows = {row["group"]: row for row in ext_n14_summary["rows"]}
    n14_delta_ext2 = float(n14_rows["method"]["mean"] - n14_rows["ext2"]["mean"])

    effects_ext2 = next(
        (row for row in ext_n14_effects["rows"] if row["comparator_group"] == "ext2"),
        None,
    )
    if effects_ext2 is None:
        raise SystemExit("Missing method vs ext2 row in n14 effects report.")

    delta_ci = float(effects_ext2["delta_ci95_halfwidth"])
    signal_to_ci = n14_delta_ext2 / max(delta_ci, 1e-9)

    rel_tail_ref = float(rel_n14["reference"]["failure_tail_rate"])
    rel_tail_cmp = float(rel_n14["comparator"]["failure_tail_rate"])
    rel_tail_improve = rel_tail_cmp - rel_tail_ref
    rel_cvar_delta = float(rel_n14["reference"]["cvar40"] - rel_n14["comparator"]["cvar40"])

    empirical_cov = float(uncertainty["assumption_fit"]["empirical_coverage"])
    pearson_r = float(uncertainty["linear_relation"]["pearson_r"])

    criteria: List[Dict] = []
    criteria.append(
        {
            "criterion": "recognized_benchmark_strength",
            "score": round(clamp_score(4.0 + 20.0 * shifted_gap_ext2), 2),
            "evidence": f"MetaWorld shifted method-ext2 delta={shifted_gap_ext2:.4f}",
            "issue": "none" if shifted_gap_ext2 >= 0.15 else "Benchmark win is not large enough.",
            "fix": "Expand benchmark breadth and preserve strong shifted margins.",
        }
    )
    criteria.append(
        {
            "criterion": "custom_track_practical_margin",
            "score": round(clamp_score(3.0 + 250.0 * n14_delta_ext2), 2),
            "evidence": f"Scenario-model n14 method-ext2 delta={n14_delta_ext2:.4f}",
            "issue": "Delta remains practically small against strongest comparator.",
            "fix": "De-emphasize mean-win language; prioritize reliability-floor claims and stronger stress slices.",
        }
    )
    criteria.append(
        {
            "criterion": "statistical_rigor",
            "score": round(clamp_score(4.0 + 1.2 * signal_to_ci), 2),
            "evidence": f"Delta/CI95={signal_to_ci:.2f} (n14 full external run)",
            "issue": "none" if signal_to_ci >= 3.0 else "Confidence margin is still weak.",
            "fix": "Increase seeds further or report narrower claim scope.",
        }
    )
    criteria.append(
        {
            "criterion": "reliability_floor_value",
            "score": round(clamp_score(4.0 + 25.0 * rel_cvar_delta + 20.0 * rel_tail_improve), 2),
            "evidence": (
                f"Tail-rate improvement={rel_tail_improve:.4f}, "
                f"CVaR40 delta={rel_cvar_delta:.4f}"
            ),
            "issue": "none" if rel_tail_improve > 0 else "No tail-risk reduction signal.",
            "fix": "Strengthen worst-case perturbation evidence and failure-taxonomy mapping.",
        }
    )
    criteria.append(
        {
            "criterion": "theory_experiment_coupling",
            "score": round(clamp_score(3.5 + 4.0 * empirical_cov + 2.0 * pearson_r), 2),
            "evidence": f"uncertainty coverage={empirical_cov:.3f}, pearson_r={pearson_r:.3f}",
            "issue": "none" if empirical_cov >= 0.9 else "Assumption coverage needs better support.",
            "fix": "Add additional diagnostics or weaken theory claims.",
        }
    )
    criteria.append(
        {
            "criterion": "external_validity",
            "score": 4.0,
            "evidence": "No hardware validation; sim/scenario-model scoped only.",
            "issue": "Primary reviewer risk for IROS manipulation framing.",
            "fix": "Reframe as algorithmic reliability and keep deployment claims tightly bounded.",
        }
    )
    criteria.append(
        {
            "criterion": "reproducibility_packaging",
            "score": 9.0,
            "evidence": "Validation stack, deterministic configs, logs/reports, Docker TeX pipeline.",
            "issue": "none",
            "fix": "Maintain artifact paths and rerun checks pre-submission.",
        }
    )

    ranked = sorted(criteria, key=lambda row: row["score"])
    backlog = []
    for row in ranked:
        if row["score"] >= 8.5:
            continue
        backlog.append(
            {
                "criterion": row["criterion"],
                "score": row["score"],
                "priority": score_to_priority(row["score"]),
                "issue": row["issue"],
                "action": row["fix"],
            }
        )

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "metrics": {
            "metaworld_shifted_gap_ext2": shifted_gap_ext2,
            "custom_n14_delta_ext2": n14_delta_ext2,
            "custom_n14_delta_ci95_halfwidth": delta_ci,
            "custom_n14_signal_to_ci": signal_to_ci,
            "reliability_tail_rate_improvement": rel_tail_improve,
            "reliability_cvar40_delta": rel_cvar_delta,
            "uncertainty_empirical_coverage": empirical_cov,
            "uncertainty_pearson_r": pearson_r,
        },
        "criteria": criteria,
        "ranked_low_to_high": ranked,
        "backlog": backlog,
    }

    out_json = pathlib.Path(args.output_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    lines: List[str] = []
    lines.append("# CORE Paper Quality Assessment")
    lines.append("")
    lines.append(f"- Generated: `{payload['generated_at_utc']}`")
    lines.append("- Scope: manuscript + current software/benchmark evidence artifacts.")
    lines.append("")
    lines.append("## Ranked Criteria (0-10)")
    lines.append("")
    lines.append("| Rank | Criterion | Score | Evidence |")
    lines.append("|---:|---|---:|---|")
    for idx, row in enumerate(ranked, start=1):
        lines.append(f"| {idx} | {row['criterion']} | {row['score']:.2f} | {row['evidence']} |")

    lines.append("")
    lines.append("## Priority Backlog")
    lines.append("")
    lines.append("| Priority | Criterion | Score | Issue | Action |")
    lines.append("|---|---|---:|---|---|")
    if backlog:
        for row in backlog:
            lines.append(
                f"| {row['priority']} | {row['criterion']} | {row['score']:.2f} | {row['issue']} | {row['action']} |"
            )
    else:
        lines.append("| P3 | none | 10.00 | No immediate gaps found. | Maintain current quality controls. |")

    out_md = pathlib.Path(args.output_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
