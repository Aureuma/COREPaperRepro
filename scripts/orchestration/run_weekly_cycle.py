#!/usr/bin/env python3
"""Run the weekly closed-loop research cycle pipeline."""

from __future__ import annotations

import datetime as dt
import pathlib
import shutil
import subprocess


def run(cmd: list[str], cwd: pathlib.Path) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


def run_py(cwd: pathlib.Path, script: str, *args: str) -> None:
    venv_python = cwd / ".venv/bin/python"
    python_bin = str(venv_python) if venv_python.is_file() else "python3"
    run([python_bin, script, *args], cwd)


def main() -> int:
    root = pathlib.Path(__file__).resolve().parents[2]
    date_tag = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    snapshot_name = f"arxiv_{date_tag}"

    metadata_dir = root / "data/papers/metadata"
    raw_dir = root / f"data/papers/raw/{snapshot_name}"
    ingested_dir = root / f"data/papers/ingested/{snapshot_name}"
    metadata_current = metadata_dir / f"{snapshot_name}.jsonl"
    metadata_latest = metadata_dir / "arxiv_latest.jsonl"
    metadata_previous = metadata_dir / "arxiv_previous.jsonl"
    ingested_records = root / f"data/papers/ingested/{snapshot_name}_records.jsonl"

    for directory in (
        metadata_dir,
        root / "data/papers/raw",
        root / "data/papers/ingested",
        root / "output/corepaper_reports/literature",
        root / "output/corepaper_reports/experiments",
    ):
        directory.mkdir(parents=True, exist_ok=True)

    if metadata_latest.is_file():
        shutil.copy2(metadata_latest, metadata_previous)

    run_py(
        root,
        "scripts/literature/fetch_arxiv.py",
        "--config",
        "config/literature_queries.json",
        "--max-results",
        "10",
        "--download-format",
        "html",
        "--metadata-out",
        str(metadata_current.relative_to(root)),
        "--download-dir",
        str(raw_dir.relative_to(root)),
    )
    shutil.copy2(metadata_current, metadata_latest)

    run_py(
        root,
        "scripts/literature/ingest_documents.py",
        "--input-dir",
        str(raw_dir.relative_to(root)),
        "--output-dir",
        str(ingested_dir.relative_to(root)),
        "--records-out",
        str(ingested_records.relative_to(root)),
    )
    shutil.copy2(ingested_records, root / "data/papers/ingested/arxiv_latest_records.jsonl")

    run_py(
        root,
        "scripts/literature/generate_weekly_delta.py",
        "--current",
        "data/papers/metadata/arxiv_latest.jsonl",
        "--previous",
        "data/papers/metadata/arxiv_previous.jsonl",
        "--output",
        "output/corepaper_reports/literature/weekly_delta_latest.md",
    )
    run_py(
        root,
        "scripts/literature/build_coverage_matrix.py",
        "--metadata",
        "data/papers/metadata/arxiv_latest.jsonl",
        "--output",
        "output/corepaper_reports/literature/coverage_matrix_latest.md",
    )
    run_py(
        root,
        "scripts/literature/extract_structured_evidence.py",
        "--metadata",
        "data/papers/metadata/arxiv_latest.jsonl",
        "--ingested-records",
        "data/papers/ingested/arxiv_latest_records.jsonl",
        "--output-jsonl",
        "data/papers/structured/evidence_latest.jsonl",
        "--output-md",
        "output/corepaper_reports/literature/evidence_table_latest.md",
    )
    run_py(
        root,
        "scripts/literature/generate_weekly_brief.py",
        "--metadata",
        "data/papers/metadata/arxiv_latest.jsonl",
        "--structured-evidence",
        "data/papers/structured/evidence_latest.jsonl",
        "--delta",
        "output/corepaper_reports/literature/weekly_delta_latest.md",
        "--output",
        "output/corepaper_reports/literature/weekly_brief_latest.md",
    )

    run_py(
        root,
        "scripts/experiments/run_harness.py",
        "--config",
        "config/experiments_smoke.json",
        "--output-dir",
        "output/corepaper_logs/experiments/latest",
        "--clean-output-dir",
    )
    run_py(
        root,
        "scripts/experiments/generate_regression_dashboard.py",
        "--logs-dir",
        "output/corepaper_logs/experiments/latest",
        "--output",
        "output/corepaper_reports/experiments/regression_dashboard_latest.md",
    )
    run_py(
        root,
        "scripts/experiments/check_artifact_integrity.py",
        "--config",
        "config/experiments_smoke.json",
        "--logs-dir",
        "output/corepaper_logs/experiments/latest",
        "--output",
        "output/corepaper_reports/experiments/integrity_report_latest.json",
    )
    run_py(
        root,
        "scripts/experiments/summarize_suite.py",
        "--logs-dir",
        "output/corepaper_logs/experiments/latest",
        "--output-json",
        "output/corepaper_reports/experiments/summary_latest.json",
        "--output-md",
        "output/corepaper_reports/experiments/summary_latest.md",
    )
    run_py(root, "scripts/experiments/generate_benchmark_configs.py")

    run_py(
        root,
        "scripts/experiments/run_harness.py",
        "--config",
        "config/benchmarks/experiments_external_baselines.json",
        "--output-dir",
        "output/corepaper_logs/experiments/external_latest",
        "--clean-output-dir",
    )
    run_py(
        root,
        "scripts/experiments/analyze_external_baselines.py",
        "--logs-dir",
        "output/corepaper_logs/experiments/external_latest",
        "--output-json",
        "output/corepaper_reports/ws3/external_baseline_summary.json",
        "--output-md",
        "output/corepaper_reports/ws3/external_baseline_summary.md",
    )
    run_py(
        root,
        "scripts/experiments/run_harness.py",
        "--config",
        "config/benchmarks/experiments_external_baselines_n14.json",
        "--output-dir",
        "output/corepaper_logs/experiments/external_n14_latest",
        "--clean-output-dir",
    )
    run_py(
        root,
        "scripts/experiments/analyze_external_baselines.py",
        "--logs-dir",
        "output/corepaper_logs/experiments/external_n14_latest",
        "--output-json",
        "output/corepaper_reports/ws3/corepaper_external_n14_summary.json",
        "--output-md",
        "output/corepaper_reports/ws3/corepaper_external_n14_summary.md",
    )
    run_py(
        root,
        "scripts/experiments/compute_effect_sizes.py",
        "--logs-dir",
        "output/corepaper_logs/experiments/external_n14_latest",
        "--output-json",
        "output/corepaper_reports/ws5/corepaper_external_n14_statistical_effects.json",
        "--output-md",
        "output/corepaper_reports/ws5/corepaper_external_n14_statistical_effects.md",
    )
    run_py(
        root,
        "scripts/experiments/analyze_pvalue_corrections.py",
        "--input-json",
        "output/corepaper_reports/ws5/corepaper_external_n14_statistical_effects.json",
        "--output-json",
        "output/corepaper_reports/ws5/pvalue_corrections_custom_n14.json",
        "--output-md",
        "output/corepaper_reports/ws5/pvalue_corrections_custom_n14.md",
        "--family-name",
        "custom-scenario-n14",
        "--rows-key",
        "rows",
    )
    run_py(
        root,
        "scripts/experiments/analyze_reliability_floor.py",
        "--logs-dir",
        "output/corepaper_logs/experiments/external_n14_latest",
        "--reference-group",
        "method",
        "--comparator-group",
        "ext2",
        "--output-json",
        "output/corepaper_reports/ws5/corepaper_reliability_floor_n14.json",
        "--output-md",
        "output/corepaper_reports/ws5/corepaper_reliability_floor_n14.md",
    )
    run_py(
        root,
        "scripts/experiments/analyze_baseline_calibration.py",
        "--summary-json",
        "output/corepaper_reports/ws3/external_baseline_summary.json",
        "--targets-json",
        "config/benchmarks/baseline_calibration_targets.json",
        "--output-json",
        "output/corepaper_reports/ws3/baseline_calibration.json",
        "--output-md",
        "output/corepaper_reports/ws3/baseline_calibration.md",
    )
    run_py(
        root,
        "scripts/experiments/compute_effect_sizes.py",
        "--logs-dir",
        "output/corepaper_logs/experiments/external_latest",
        "--output-json",
        "output/corepaper_reports/ws5/statistical_effects.json",
        "--output-md",
        "output/corepaper_reports/ws5/statistical_effects.md",
    )
    run_py(
        root,
        "scripts/experiments/analyze_statistical_power.py",
        "--effects-json",
        "output/corepaper_reports/ws5/statistical_effects.json",
        "--target-power",
        "0.80",
        "--alpha",
        "0.05",
        "--sigma-floor",
        "0.005",
        "--output-json",
        "output/corepaper_reports/ws5/statistical_power.json",
        "--output-md",
        "output/corepaper_reports/ws5/statistical_power.md",
    )

    run_py(
        root,
        "scripts/experiments/run_harness.py",
        "--config",
        "config/benchmarks/experiments_ablation.json",
        "--output-dir",
        "output/corepaper_logs/experiments/ablation_latest",
        "--clean-output-dir",
    )
    run_py(
        root,
        "scripts/experiments/analyze_ablation.py",
        "--logs-dir",
        "output/corepaper_logs/experiments/ablation_latest",
        "--output-json",
        "output/corepaper_reports/ws5/ablation_results.json",
        "--output-md",
        "output/corepaper_reports/ws5/ablation_results.md",
    )

    run_py(
        root,
        "scripts/experiments/run_harness.py",
        "--config",
        "config/benchmarks/experiments_robustness.json",
        "--output-dir",
        "output/corepaper_logs/experiments/robustness_latest",
        "--clean-output-dir",
    )
    run_py(
        root,
        "scripts/experiments/analyze_robustness.py",
        "--logs-dir",
        "output/corepaper_logs/experiments/robustness_latest",
        "--nominal-summary",
        "output/corepaper_reports/experiments/summary_latest.json",
        "--output-json",
        "output/corepaper_reports/ws5/robustness_results.json",
        "--output-md",
        "output/corepaper_reports/ws5/robustness_results.md",
    )

    run_py(
        root,
        "scripts/experiments/run_harness.py",
        "--config",
        "config/benchmarks/experiments_software_transfer.json",
        "--output-dir",
        "output/corepaper_logs/experiments/software_transfer_latest",
        "--clean-output-dir",
    )
    run_py(
        root,
        "scripts/experiments/analyze_software_transfer.py",
        "--logs-dir",
        "output/corepaper_logs/experiments/software_transfer_latest",
        "--nominal-summary",
        "output/corepaper_reports/experiments/summary_latest.json",
        "--output-json",
        "output/corepaper_reports/ws5/software_transfer_results.json",
        "--output-md",
        "output/corepaper_reports/ws5/software_transfer_results.md",
    )

    run_py(
        root,
        "scripts/experiments/run_harness.py",
        "--config",
        "config/benchmarks/experiments_sim2sim.json",
        "--output-dir",
        "output/corepaper_logs/experiments/sim2sim_latest",
        "--clean-output-dir",
    )
    run_py(
        root,
        "scripts/experiments/analyze_sim2sim.py",
        "--logs-dir",
        "output/corepaper_logs/experiments/sim2sim_latest",
        "--nominal-summary",
        "output/corepaper_reports/experiments/summary_latest.json",
        "--output-json",
        "output/corepaper_reports/ws5/sim2sim_transfer_results.json",
        "--output-md",
        "output/corepaper_reports/ws5/sim2sim_transfer_results.md",
    )

    run_py(
        root,
        "scripts/experiments/run_metaworld_slice.py",
        "--config",
        "config/benchmarks/experiments_metaworld_slice.json",
        "--output-json",
        "output/corepaper_reports/ws3/metaworld_slice_results.json",
        "--output-md",
        "output/corepaper_reports/ws3/metaworld_slice_results.md",
    )
    run_py(
        root,
        "scripts/experiments/analyze_metaworld_slice_stats.py",
        "--input-json",
        "output/corepaper_reports/ws3/metaworld_slice_results.json",
        "--output-json",
        "output/corepaper_reports/ws3/metaworld_slice_stats.json",
        "--output-md",
        "output/corepaper_reports/ws3/metaworld_slice_stats.md",
    )
    run_py(
        root,
        "scripts/experiments/run_metaworld_slice.py",
        "--config",
        "config/benchmarks/experiments_metaworld_seedexp_latency_method_n30.json",
        "--output-json",
        "output/corepaper_reports/ws3/metaworld_seedexp_latency_method_n30_results.json",
        "--output-md",
        "output/corepaper_reports/ws3/metaworld_seedexp_latency_method_n30_results.md",
    )
    run_py(
        root,
        "scripts/experiments/analyze_metaworld_slice_stats.py",
        "--input-json",
        "output/corepaper_reports/ws3/metaworld_seedexp_latency_method_n30_results.json",
        "--output-json",
        "output/corepaper_reports/ws3/metaworld_seedexp_latency_method_n30_stats.json",
        "--output-md",
        "output/corepaper_reports/ws3/metaworld_seedexp_latency_method_n30_stats.md",
        "--comparators",
        "latency_aware",
    )
    run_py(
        root,
        "scripts/experiments/analyze_cvar_alpha_sensitivity.py",
        "--input-json",
        "output/corepaper_reports/ws3/metaworld_seedexp_latency_method_n30_results.json",
        "--reference-group",
        "method",
        "--comparator-group",
        "latency_aware",
        "--alphas",
        "0.1,0.2,0.3,0.4,0.5",
        "--output-json",
        "output/corepaper_reports/ws5/metaworld_cvar_sensitivity_latency_n30.json",
        "--output-md",
        "output/corepaper_reports/ws5/metaworld_cvar_sensitivity_latency_n30.md",
    )
    run_py(
        root,
        "scripts/experiments/analyze_reliability_floor.py",
        "--logs-dir",
        "output/corepaper_logs/experiments/external_latest",
        "--reference-group",
        "method",
        "--comparator-group",
        "ext2",
        "--output-json",
        "output/corepaper_reports/ws5/reliability_floor.json",
        "--output-md",
        "output/corepaper_reports/ws5/reliability_floor.md",
    )
    run_py(
        root,
        "scripts/experiments/analyze_gate_threshold_sensitivity.py",
        "--cycles-dir",
        "output/corepaper_logs/ws4/cycles",
        "--tau-green-list",
        "0.01,0.02,0.04",
        "--tau-yellow-list",
        "0.003,0.005,0.01,0.02",
        "--output-json",
        "output/corepaper_reports/ws5/gate_threshold_sensitivity.json",
        "--output-md",
        "output/corepaper_reports/ws5/gate_threshold_sensitivity.md",
    )
    run_py(
        root,
        "scripts/experiments/analyze_uncertainty_dominance.py",
        "--logs-dirs",
        (
            "output/corepaper_logs/experiments/external_latest,"
            "output/corepaper_logs/experiments/robustness_latest,"
            "output/corepaper_logs/experiments/software_transfer_latest,"
            "output/corepaper_logs/experiments/sim2sim_latest"
        ),
        "--output-json",
        "output/corepaper_reports/ws5/uncertainty_dominance.json",
        "--output-md",
        "output/corepaper_reports/ws5/uncertainty_dominance.md",
    )
    run_py(
        root,
        "scripts/experiments/analyze_uncertainty_misspec_sensitivity.py",
        "--logs-dirs",
        (
            "output/corepaper_logs/experiments/external_latest,"
            "output/corepaper_logs/experiments/robustness_latest,"
            "output/corepaper_logs/experiments/software_transfer_latest,"
            "output/corepaper_logs/experiments/sim2sim_latest,"
            "output/corepaper_logs/experiments/recent_baselines_latest"
        ),
        "--uncertainty-json",
        "output/corepaper_reports/ws5/uncertainty_dominance.json",
        "--output-json",
        "output/corepaper_reports/ws5/uncertainty_misspec_sensitivity.json",
        "--output-md",
        "output/corepaper_reports/ws5/uncertainty_misspec_sensitivity.md",
    )
    run_py(
        root,
        "scripts/experiments/analyze_seed_expansion.py",
        "--variant-a",
        "method",
        "--variant-b",
        "ext2",
        "--scenario",
        "nominal",
        "--seed-start",
        "1",
        "--seed-end",
        "14",
        "--output-json",
        "output/corepaper_reports/ws5/seed_expansion_method_vs_ext2.json",
        "--output-md",
        "output/corepaper_reports/ws5/seed_expansion_method_vs_ext2.md",
    )

    run_py(root, "scripts/figures/generate_paper_figures.py")
    run_py(root, "scripts/figures/export_png_figures.py", "--with-png")
    run_py(root, "scripts/vis/build_video_pipeline.py")

    run_py(root, "scripts/paper/generate_draft_manuscript.py")
    run_py(
        root,
        "scripts/paper/generate_simple_pdf.py",
        "--input",
        "output/corepaper_submission/corepaper_main_paper_draft.md",
        "--output",
        "output/corepaper_submission/corepaper_main_paper_draft.pdf",
        "--title",
        "CORE Paper Draft",
    )
    run_py(root, "scripts/paper/build_submission_bundle.py", "--bundle-dir", "output/corepaper_submission")
    run_py(
        root,
        "scripts/review_readiness/build_anonymous_release.py",
        "--output-zip",
        "output/corepaper_submission/corepaper_anonymous_release.zip",
    )

    run_py(
        root,
        "scripts/ws4/run_cycle_from_summary.py",
        "--summary-json",
        "output/corepaper_reports/experiments/summary_latest.json",
        "--cycle-id",
        f"cycle-{date_tag}",
        "--hypothesis-id",
        "H1",
        "--notes",
        "Automated weekly cycle from multiseed experiment summary",
    )
    run_py(root, "scripts/review_readiness/run_repro_audit.py", "--output", "docs/review_readiness/repro-audit-report.md")
    run_py(root, "scripts/validate_all.py")

    print(f"Weekly research cycle completed for {date_tag}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
