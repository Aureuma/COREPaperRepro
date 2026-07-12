#!/usr/bin/env python3
"""Validate WS3 experiment stack artifacts."""

from __future__ import annotations

import json
import pathlib
import sys
from typing import List


ROOT = pathlib.Path(__file__).resolve().parents[2]


def main() -> int:
    errors: List[str] = []

    required_files = [
        ROOT / "docs/plan.md",
        ROOT / "config/experiments_smoke.json",
        ROOT / "config/benchmarks/experiments_external_baselines.json",
        ROOT / "config/benchmarks/experiments_ablation.json",
        ROOT / "config/benchmarks/experiments_robustness.json",
        ROOT / "config/benchmarks/experiments_software_transfer.json",
        ROOT / "config/benchmarks/experiments_sim2sim.json",
        ROOT / "config/benchmarks/experiments_recent_paper_baselines.json",
        ROOT / "config/benchmarks/experiments_metaworld_recent_baselines.json",
        ROOT / "config/benchmarks/experiments_metaworld_seedexp_ext2_method.json",
        ROOT / "config/benchmarks/experiments_metaworld_seedexp_latency_method.json",
        ROOT / "config/benchmarks/experiments_metaworld_seedexp_adaptmanip_method.json",
        ROOT / "config/benchmarks/experiments_metaworld_seedexp_adaptmanip_method_n30.json",
        ROOT / "config/benchmarks/baseline_calibration_targets.json",
        ROOT / "scripts/experiments/software_benchmark.py",
        ROOT / "scripts/experiments/mock_experiment.py",
        ROOT / "scripts/experiments/external_baseline_impl.py",
        ROOT / "scripts/experiments/run_harness.py",
        ROOT / "scripts/experiments/generate_regression_dashboard.py",
        ROOT / "scripts/experiments/check_artifact_integrity.py",
        ROOT / "scripts/experiments/summarize_suite.py",
        ROOT / "scripts/experiments/generate_benchmark_configs.py",
        ROOT / "scripts/experiments/analyze_external_baselines.py",
        ROOT / "scripts/experiments/analyze_baseline_calibration.py",
        ROOT / "scripts/experiments/compute_effect_sizes.py",
        ROOT / "scripts/experiments/analyze_statistical_power.py",
        ROOT / "scripts/experiments/analyze_ablation.py",
        ROOT / "scripts/experiments/analyze_robustness.py",
        ROOT / "scripts/experiments/analyze_software_transfer.py",
        ROOT / "scripts/experiments/analyze_sim2sim.py",
        ROOT / "scripts/experiments/analyze_pvalue_corrections.py",
        ROOT / "scripts/experiments/analyze_recent_paper_baselines.py",
        ROOT / "scripts/experiments/summarize_validity_gap.py",
        ROOT / "scripts/experiments/run_metaworld_slice.py",
        ROOT / "scripts/experiments/analyze_metaworld_slice_stats.py",
        ROOT / "scripts/experiments/analyze_gate_threshold_sensitivity.py",
        ROOT / "scripts/experiments/analyze_reliability_floor.py",
        ROOT / "scripts/experiments/analyze_uncertainty_dominance.py",
        ROOT / "scripts/experiments/analyze_uncertainty_misspec_sensitivity.py",
        ROOT / "scripts/experiments/analyze_prop2_ordering.py",
        ROOT / "scripts/experiments/analyze_budget_parity.py",
        ROOT / "scripts/experiments/analyze_theorem1_neff.py",
        ROOT / "scripts/experiments/analyze_seed_expansion.py",
        ROOT / "scripts/paper/generate_result_macros.py",
    ]
    for path in required_files:
        if not path.is_file():
            errors.append(f"Missing file: {path}")

    if errors:
        for e in errors:
            print(e, file=sys.stderr)
        return 1

    plan_text = (ROOT / "docs/plan.md").read_text(encoding="utf-8")
    for marker in (
        "## Source: `docs/ws3/benchmark-protocol.md`",
        "## Source: `docs/ws3/baseline-replication-report.md`",
    ):
        if marker not in plan_text:
            errors.append(f"Missing consolidated marker in docs/plan.md: {marker}")

    config = json.loads((ROOT / "config/experiments_smoke.json").read_text(encoding="utf-8"))
    runs = config.get("runs", [])
    if not runs:
        errors.append("config/experiments_smoke.json must contain at least one run")

    report = ROOT / "output/corepaper_reports/experiments/regression_dashboard_latest.md"
    if not report.is_file():
        errors.append("Missing generated report: output/corepaper_reports/experiments/regression_dashboard_latest.md")

    integrity = ROOT / "output/corepaper_reports/experiments/integrity_report_latest.json"
    if not integrity.is_file():
        errors.append("Missing generated report: output/corepaper_reports/experiments/integrity_report_latest.json")
    summary_md = ROOT / "output/corepaper_reports/experiments/summary_latest.md"
    if not summary_md.is_file():
        errors.append("Missing generated report: output/corepaper_reports/experiments/summary_latest.md")
    summary_json = ROOT / "output/corepaper_reports/experiments/summary_latest.json"
    if not summary_json.is_file():
        errors.append("Missing generated report: output/corepaper_reports/experiments/summary_latest.json")
    external_md = ROOT / "output/corepaper_reports/ws3/external_baseline_summary.md"
    if not external_md.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws3/external_baseline_summary.md")
    external_json = ROOT / "output/corepaper_reports/ws3/external_baseline_summary.json"
    if not external_json.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws3/external_baseline_summary.json")
    calibration_md = ROOT / "output/corepaper_reports/ws3/baseline_calibration.md"
    if not calibration_md.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws3/baseline_calibration.md")
    calibration_json = ROOT / "output/corepaper_reports/ws3/baseline_calibration.json"
    if not calibration_json.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws3/baseline_calibration.json")
    metaworld_md = ROOT / "output/corepaper_reports/ws3/metaworld_slice_results.md"
    if not metaworld_md.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws3/metaworld_slice_results.md")
    metaworld_json = ROOT / "output/corepaper_reports/ws3/metaworld_slice_results.json"
    if not metaworld_json.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws3/metaworld_slice_results.json")
    metaworld_stats_md = ROOT / "output/corepaper_reports/ws3/metaworld_slice_stats.md"
    if not metaworld_stats_md.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws3/metaworld_slice_stats.md")
    metaworld_stats_json = ROOT / "output/corepaper_reports/ws3/metaworld_slice_stats.json"
    if not metaworld_stats_json.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws3/metaworld_slice_stats.json")
    stats_md = ROOT / "output/corepaper_reports/ws5/statistical_effects.md"
    if not stats_md.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws5/statistical_effects.md")
    stats_json = ROOT / "output/corepaper_reports/ws5/statistical_effects.json"
    if not stats_json.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws5/statistical_effects.json")
    power_md = ROOT / "output/corepaper_reports/ws5/statistical_power.md"
    if not power_md.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws5/statistical_power.md")
    power_json = ROOT / "output/corepaper_reports/ws5/statistical_power.json"
    if not power_json.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws5/statistical_power.json")
    pvals_custom_md = ROOT / "output/corepaper_reports/ws5/pvalue_corrections_custom_n5.md"
    if not pvals_custom_md.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws5/pvalue_corrections_custom_n5.md")
    pvals_custom_json = ROOT / "output/corepaper_reports/ws5/pvalue_corrections_custom_n5.json"
    if not pvals_custom_json.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws5/pvalue_corrections_custom_n5.json")
    seedexp_md = ROOT / "output/corepaper_reports/ws5/seed_expansion_method_vs_ext2.md"
    if not seedexp_md.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws5/seed_expansion_method_vs_ext2.md")
    seedexp_json = ROOT / "output/corepaper_reports/ws5/seed_expansion_method_vs_ext2.json"
    if not seedexp_json.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws5/seed_expansion_method_vs_ext2.json")
    ablation_md = ROOT / "output/corepaper_reports/ws5/ablation_results.md"
    if not ablation_md.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws5/ablation_results.md")
    ablation_json = ROOT / "output/corepaper_reports/ws5/ablation_results.json"
    if not ablation_json.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws5/ablation_results.json")
    robustness_md = ROOT / "output/corepaper_reports/ws5/robustness_results.md"
    if not robustness_md.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws5/robustness_results.md")
    robustness_json = ROOT / "output/corepaper_reports/ws5/robustness_results.json"
    if not robustness_json.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws5/robustness_results.json")
    software_transfer_md = ROOT / "output/corepaper_reports/ws5/software_transfer_results.md"
    if not software_transfer_md.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws5/software_transfer_results.md")
    software_transfer_json = ROOT / "output/corepaper_reports/ws5/software_transfer_results.json"
    if not software_transfer_json.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws5/software_transfer_results.json")
    sim2sim_transfer_md = ROOT / "output/corepaper_reports/ws5/sim2sim_transfer_results.md"
    if not sim2sim_transfer_md.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws5/sim2sim_transfer_results.md")
    sim2sim_transfer_json = ROOT / "output/corepaper_reports/ws5/sim2sim_transfer_results.json"
    if not sim2sim_transfer_json.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws5/sim2sim_transfer_results.json")
    recent_baselines_md = ROOT / "output/corepaper_reports/ws5/recent_paper_baselines.md"
    if not recent_baselines_md.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws5/recent_paper_baselines.md")
    recent_baselines_json = ROOT / "output/corepaper_reports/ws5/recent_paper_baselines.json"
    if not recent_baselines_json.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws5/recent_paper_baselines.json")
    pvals_recent_md = ROOT / "output/corepaper_reports/ws5/pvalue_corrections_recent_stress.md"
    if not pvals_recent_md.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws5/pvalue_corrections_recent_stress.md")
    pvals_recent_json = ROOT / "output/corepaper_reports/ws5/pvalue_corrections_recent_stress.json"
    if not pvals_recent_json.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws5/pvalue_corrections_recent_stress.json")
    gate_md = ROOT / "output/corepaper_reports/ws5/gate_threshold_sensitivity.md"
    if not gate_md.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws5/gate_threshold_sensitivity.md")
    gate_json = ROOT / "output/corepaper_reports/ws5/gate_threshold_sensitivity.json"
    if not gate_json.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws5/gate_threshold_sensitivity.json")
    reliability_md = ROOT / "output/corepaper_reports/ws5/reliability_floor.md"
    if not reliability_md.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws5/reliability_floor.md")
    reliability_json = ROOT / "output/corepaper_reports/ws5/reliability_floor.json"
    if not reliability_json.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws5/reliability_floor.json")
    uncertainty_md = ROOT / "output/corepaper_reports/ws5/uncertainty_dominance.md"
    if not uncertainty_md.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws5/uncertainty_dominance.md")
    uncertainty_json = ROOT / "output/corepaper_reports/ws5/uncertainty_dominance.json"
    if not uncertainty_json.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws5/uncertainty_dominance.json")
    uncertainty_misspec_md = ROOT / "output/corepaper_reports/ws5/uncertainty_misspec_sensitivity.md"
    if not uncertainty_misspec_md.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws5/uncertainty_misspec_sensitivity.md")
    uncertainty_misspec_json = ROOT / "output/corepaper_reports/ws5/uncertainty_misspec_sensitivity.json"
    if not uncertainty_misspec_json.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws5/uncertainty_misspec_sensitivity.json")
    prop2_proxy_md = ROOT / "output/corepaper_reports/ws5/prop2_ordering_proxy.md"
    if not prop2_proxy_md.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws5/prop2_ordering_proxy.md")
    prop2_proxy_json = ROOT / "output/corepaper_reports/ws5/prop2_ordering_proxy.json"
    if not prop2_proxy_json.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws5/prop2_ordering_proxy.json")
    budget_parity_md = ROOT / "output/corepaper_reports/ws5/metaworld_budget_parity.md"
    if not budget_parity_md.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws5/metaworld_budget_parity.md")
    budget_parity_json = ROOT / "output/corepaper_reports/ws5/metaworld_budget_parity.json"
    if not budget_parity_json.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws5/metaworld_budget_parity.json")
    theorem1_neff_md = ROOT / "output/corepaper_reports/ws5/theorem1_neff_diagnostic.md"
    if not theorem1_neff_md.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws5/theorem1_neff_diagnostic.md")
    theorem1_neff_json = ROOT / "output/corepaper_reports/ws5/theorem1_neff_diagnostic.json"
    if not theorem1_neff_json.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws5/theorem1_neff_diagnostic.json")
    metaworld_recent_md = ROOT / "output/corepaper_reports/ws3/metaworld_recent_baselines_stats.md"
    if not metaworld_recent_md.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws3/metaworld_recent_baselines_stats.md")
    metaworld_recent_json = ROOT / "output/corepaper_reports/ws3/metaworld_recent_baselines_stats.json"
    if not metaworld_recent_json.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws3/metaworld_recent_baselines_stats.json")
    metaworld_seedexp_md = ROOT / "output/corepaper_reports/ws3/metaworld_seedexp_ext2_method_stats.md"
    if not metaworld_seedexp_md.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws3/metaworld_seedexp_ext2_method_stats.md")
    metaworld_seedexp_json = ROOT / "output/corepaper_reports/ws3/metaworld_seedexp_ext2_method_stats.json"
    if not metaworld_seedexp_json.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws3/metaworld_seedexp_ext2_method_stats.json")
    metaworld_seedexp_latency_md = ROOT / "output/corepaper_reports/ws3/metaworld_seedexp_latency_method_stats.md"
    if not metaworld_seedexp_latency_md.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws3/metaworld_seedexp_latency_method_stats.md")
    metaworld_seedexp_latency_json = ROOT / "output/corepaper_reports/ws3/metaworld_seedexp_latency_method_stats.json"
    if not metaworld_seedexp_latency_json.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws3/metaworld_seedexp_latency_method_stats.json")
    metaworld_seedexp_adapt_md = ROOT / "output/corepaper_reports/ws3/metaworld_seedexp_adaptmanip_method_stats.md"
    if not metaworld_seedexp_adapt_md.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws3/metaworld_seedexp_adaptmanip_method_stats.md")
    metaworld_seedexp_adapt_json = ROOT / "output/corepaper_reports/ws3/metaworld_seedexp_adaptmanip_method_stats.json"
    if not metaworld_seedexp_adapt_json.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws3/metaworld_seedexp_adaptmanip_method_stats.json")
    metaworld_seedexp_adapt_n30_md = ROOT / "output/corepaper_reports/ws3/metaworld_seedexp_adaptmanip_method_n30_stats.md"
    if not metaworld_seedexp_adapt_n30_md.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws3/metaworld_seedexp_adaptmanip_method_n30_stats.md")
    metaworld_seedexp_adapt_n30_json = ROOT / "output/corepaper_reports/ws3/metaworld_seedexp_adaptmanip_method_n30_stats.json"
    if not metaworld_seedexp_adapt_n30_json.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws3/metaworld_seedexp_adaptmanip_method_n30_stats.json")
    pvals_meta_recent_md = ROOT / "output/corepaper_reports/ws3/pvalue_corrections_metaworld_recent.md"
    if not pvals_meta_recent_md.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws3/pvalue_corrections_metaworld_recent.md")
    pvals_meta_recent_json = ROOT / "output/corepaper_reports/ws3/pvalue_corrections_metaworld_recent.json"
    if not pvals_meta_recent_json.is_file():
        errors.append("Missing generated report: output/corepaper_reports/ws3/pvalue_corrections_metaworld_recent.json")
    validity_gap_md = ROOT / "output/corepaper_reports/review_readiness/validity_gap_status.md"
    if not validity_gap_md.is_file():
        errors.append("Missing generated report: output/corepaper_reports/review_readiness/validity_gap_status.md")
    validity_gap_json = ROOT / "output/corepaper_reports/review_readiness/validity_gap_status.json"
    if not validity_gap_json.is_file():
        errors.append("Missing generated report: output/corepaper_reports/review_readiness/validity_gap_status.json")
    result_macros = ROOT / "paper/generated/results_macros.tex"
    if not result_macros.is_file():
        errors.append("Missing generated macros: paper/generated/results_macros.tex")

    if errors:
        for e in errors:
            print(e, file=sys.stderr)
        return 1

    print("WS3 experiment stack validation successful.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
