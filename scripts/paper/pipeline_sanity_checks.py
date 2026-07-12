#!/usr/bin/env python3
"""Sanity checks for pipeline outputs (artifacts + JSON shape/type constraints)."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[2]


def require_file(path: pathlib.Path, *, min_size: int = 1) -> None:
    if not path.is_file():
        raise AssertionError(f"Missing artifact: {path}")
    size = path.stat().st_size
    if size < min_size:
        raise AssertionError(f"Artifact too small ({size} bytes): {path}")


def require_file_max(path: pathlib.Path, *, max_size: int) -> None:
    if not path.is_file():
        raise AssertionError(f"Missing artifact: {path}")
    size = path.stat().st_size
    if size > max_size:
        raise AssertionError(f"Artifact too large ({size} bytes > {max_size}): {path}")


def load_json(path: pathlib.Path) -> Any:
    require_file(path, min_size=2)
    return json.loads(path.read_text(encoding="utf-8"))


def require_keys(obj: dict[str, Any], keys: list[str], *, context: str) -> None:
    for key in keys:
        if key not in obj:
            raise AssertionError(f"Missing key '{key}' in {context}")


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _check_group_rows(rows: list[Any], context: str) -> None:
    if not rows:
        raise AssertionError(f"Expected non-empty rows in {context}")
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            raise AssertionError(f"Row {i} is not an object in {context}")
        require_keys(row, ["group", "n", "mean", "std", "ci95"], context=f"{context}[{i}]")
        if not isinstance(row["group"], str) or not row["group"]:
            raise AssertionError(f"Invalid group label in {context}[{i}]")
        if not isinstance(row["n"], int) or row["n"] <= 0:
            raise AssertionError(f"Invalid n in {context}[{i}]")
        for key in ("mean", "std", "ci95"):
            if not _is_number(row[key]):
                raise AssertionError(f"Non-numeric {key} in {context}[{i}]")


def _check_comparison_rows(rows: list[Any], context: str) -> None:
    if not rows:
        raise AssertionError(f"Expected non-empty comparisons in {context}")
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            raise AssertionError(f"Comparison {i} is not an object in {context}")
        require_keys(
            row,
            [
                "reference_group",
                "comparator_group",
                "delta_mean",
                "delta_cvar40_seed",
                "delta_worst_seed_mean",
                "p_two_sided",
            ],
            context=f"{context}[{i}]",
        )
        for k in ("delta_mean", "delta_cvar40_seed", "delta_worst_seed_mean", "p_two_sided"):
            if not _is_number(row[k]):
                raise AssertionError(f"Non-numeric {k} in {context}[{i}]")


def _require_group_names(rows: list[Any], required: set[str], *, context: str) -> None:
    seen: set[str] = set()
    for row in rows:
        if isinstance(row, dict) and isinstance(row.get("group"), str):
            seen.add(row["group"])
    missing = sorted(required - seen)
    if missing:
        raise AssertionError(f"Missing groups in {context}: {', '.join(missing)}")


def _check_required_artifacts() -> None:
    main_pdf = ROOT / "paper/build/manuscript.pdf"
    # IROS CFP rule: submission PDF must be <= 6 MB.
    require_file(main_pdf, min_size=100_000)
    require_file_max(main_pdf, max_size=6 * 1024 * 1024)

    required = [
        (ROOT / "paper/generated/results_macros.tex", 2_000),
        (ROOT / "output/corepaper_reports/experiments/summary_latest.json", 200),
        (ROOT / "output/corepaper_reports/ws3/external_baseline_summary.json", 200),
        (ROOT / "output/corepaper_reports/ws3/corepaper_external_n14_summary.json", 200),
        (ROOT / "output/corepaper_reports/ws3/metaworld_slice_results.json", 1_000),
        (ROOT / "output/corepaper_reports/ws3/metaworld_slice_stats.json", 500),
        (ROOT / "output/corepaper_reports/ws3/metaworld_recent_baselines_stats.json", 500),
        (ROOT / "output/corepaper_reports/ws3/maniskill_proxy_results.json", 1_000),
        (ROOT / "output/corepaper_reports/ws3/maniskill_proxy_stats.json", 500),
        (ROOT / "output/corepaper_reports/ws3/cross_embodiment_proxy_results.json", 1_000),
        (ROOT / "output/corepaper_reports/ws3/cross_embodiment_proxy_stats.json", 500),
        (ROOT / "output/corepaper_reports/ws3/metaworld_seedexp_latency_method_n30_stats.json", 400),
        (ROOT / "output/corepaper_reports/ws3/metaworld_seedexp_adaptmanip_method_n30_stats.json", 400),
        (ROOT / "output/corepaper_reports/ws5/statistical_effects.json", 300),
        (ROOT / "output/corepaper_reports/ws5/corepaper_external_n14_statistical_effects.json", 300),
        (ROOT / "output/corepaper_reports/ws5/o2o_proxy_recent.json", 300),
        (ROOT / "output/corepaper_reports/ws5/o2o_failure_accounting.json", 200),
        (ROOT / "output/corepaper_reports/ws5/verification_first_diagnostics.json", 300),
        (ROOT / "output/corepaper_reports/ws5/adversarial_stress_results.json", 300),
        (ROOT / "output/corepaper_reports/ws5/reliability_floor.json", 100),
        (ROOT / "output/corepaper_reports/ws5/corepaper_reliability_floor_n14.json", 100),
        (ROOT / "output/corepaper_reports/ws5/metaworld_cvar_sensitivity_latency_n30.json", 200),
        (ROOT / "output/corepaper_reports/ws5/metaworld_cvar_sensitivity_adaptmanip_n30.json", 200),
        (ROOT / "output/corepaper_reports/ws5/metaworld_adapt_equivalence_n14.json", 200),
        (ROOT / "output/corepaper_reports/ws5/prop2_ordering_proxy.json", 200),
        (ROOT / "output/corepaper_reports/ws5/metaworld_budget_parity.json", 200),
        (ROOT / "output/corepaper_reports/ws5/theorem1_neff_diagnostic.json", 200),
        (ROOT / "output/corepaper_reports/ws5/uncertainty_misspec_sensitivity.json", 200),
        (ROOT / "output/corepaper_reports/ws5/library_lane.json", 300),
        (ROOT / "output/corepaper_reports/ws5/pvalue_corrections_library_lane.json", 150),
        (ROOT / "output/corepaper_reports/ws5/library_parity_official.json", 300),
        (ROOT / "output/corepaper_reports/ws5/latency_aware_official_parity_audit.json", 200),
        (ROOT / "output/corepaper_reports/ws5/sim2sim_transfer_results.json", 300),
        (ROOT / "output/corepaper_reports/ws5/pvalue_corrections_custom_n14.json", 150),
        (ROOT / "output/corepaper_reports/version_snapshot.json", 300),
    ]
    for path, min_size in required:
        require_file(path, min_size=min_size)

    png_min_sizes = {
        "F5_failure_taxonomy": 12_000,
    }
    for fig in (
        "F1_pipeline",
        "F2_main_benchmark",
        "F3_ablation",
        "F4_robustness",
        "F5_failure_taxonomy",
        "F6_baseline_calibration",
        "F7_metaworld_taskwise",
    ):
        require_file(ROOT / f"output/corepaper_assets/figures/{fig}.svg", min_size=1_000)
        require_file(
            ROOT / f"output/corepaper_assets/figures/{fig}.png",
            min_size=png_min_sizes.get(fig, 15_000),
        )


def _check_json_shapes() -> None:
    summary = load_json(ROOT / "output/corepaper_reports/experiments/summary_latest.json")
    if not isinstance(summary, dict):
        raise AssertionError("summary_latest.json must be a JSON object")
    groups = summary.get("groups")
    if not isinstance(groups, list):
        raise AssertionError("summary_latest.json.groups must be a list")
    _check_group_rows(groups, "summary_latest.json.groups")

    external = load_json(ROOT / "output/corepaper_reports/ws3/external_baseline_summary.json")
    if not isinstance(external, dict):
        raise AssertionError("external_baseline_summary.json must be a JSON object")
    rows = external.get("rows")
    if not isinstance(rows, list):
        raise AssertionError("external_baseline_summary.json.rows must be a list")
    _check_group_rows(rows, "external_baseline_summary.json.rows")
    _require_group_names(rows, {"method", "baseline", "ext1", "ext2"}, context="external_baseline_summary.json.rows")

    n14_external = load_json(ROOT / "output/corepaper_reports/ws3/corepaper_external_n14_summary.json")
    if not isinstance(n14_external, dict):
        raise AssertionError("corepaper_external_n14_summary.json must be a JSON object")
    n14_rows = n14_external.get("rows")
    if not isinstance(n14_rows, list):
        raise AssertionError("corepaper_external_n14_summary.json.rows must be a list")
    _check_group_rows(n14_rows, "corepaper_external_n14_summary.json.rows")
    _require_group_names(
        n14_rows,
        {"method", "baseline", "ext1", "ext2"},
        context="corepaper_external_n14_summary.json.rows",
    )
    n14_by_group = {
        row["group"]: row
        for row in n14_rows
        if isinstance(row, dict) and isinstance(row.get("group"), str)
    }
    for group in ("method", "ext2"):
        if int(n14_by_group[group]["n"]) < 10:
            raise AssertionError(f"corepaper_external_n14_summary.json expected >=10 seeds for {group}")

    metaworld = load_json(ROOT / "output/corepaper_reports/ws3/metaworld_slice_results.json")
    if not isinstance(metaworld, dict):
        raise AssertionError("metaworld_slice_results.json must be a JSON object")
    require_keys(
        metaworld,
        ["summary", "task_breakdown", "sample_efficiency", "episodes", "physics_randomization"],
        context="metaworld_slice_results.json",
    )
    if not isinstance(metaworld["summary"], dict):
        raise AssertionError("metaworld_slice_results.json.summary must be an object")
    require_keys(metaworld["summary"], ["nominal", "shifted"], context="metaworld_slice_results.json.summary")
    if not isinstance(metaworld["task_breakdown"], list) or not metaworld["task_breakdown"]:
        raise AssertionError("metaworld_slice_results.json.task_breakdown must be a non-empty list")
    if not isinstance(metaworld["episodes"], list) or not metaworld["episodes"]:
        raise AssertionError("metaworld_slice_results.json.episodes must be a non-empty list")

    stats = load_json(ROOT / "output/corepaper_reports/ws3/metaworld_slice_stats.json")
    if not isinstance(stats, dict):
        raise AssertionError("metaworld_slice_stats.json must be a JSON object")
    require_keys(stats, ["variant_summary", "comparisons"], context="metaworld_slice_stats.json")
    if not isinstance(stats["variant_summary"], dict) or "method" not in stats["variant_summary"]:
        raise AssertionError("metaworld_slice_stats.json.variant_summary must include method")
    comparisons = stats["comparisons"]
    if not isinstance(comparisons, list):
        raise AssertionError("metaworld_slice_stats.json.comparisons must be a list")
    _check_comparison_rows(comparisons, "metaworld_slice_stats.json.comparisons")

    recent_meta = load_json(ROOT / "output/corepaper_reports/ws3/metaworld_recent_baselines_stats.json")
    if not isinstance(recent_meta, dict):
        raise AssertionError("metaworld_recent_baselines_stats.json must be a JSON object")
    require_keys(recent_meta, ["variant_summary", "comparisons"], context="metaworld_recent_baselines_stats.json")
    if not isinstance(recent_meta["variant_summary"], dict):
        raise AssertionError("metaworld_recent_baselines_stats.json.variant_summary must be an object")
    for required_variant in ("method", "ext2", "latency_aware", "adaptmanip"):
        if required_variant not in recent_meta["variant_summary"]:
            raise AssertionError(
                f"metaworld_recent_baselines_stats.json.variant_summary missing {required_variant}"
            )

    maniskill = load_json(ROOT / "output/corepaper_reports/ws3/maniskill_proxy_results.json")
    if not isinstance(maniskill, dict):
        raise AssertionError("maniskill_proxy_results.json must be a JSON object")
    require_keys(maniskill, ["summary", "task_breakdown", "sample_efficiency", "episodes"], context="maniskill_proxy_results.json")
    if not isinstance(maniskill["episodes"], list) or not maniskill["episodes"]:
        raise AssertionError("maniskill_proxy_results.json.episodes must be a non-empty list")

    maniskill_stats = load_json(ROOT / "output/corepaper_reports/ws3/maniskill_proxy_stats.json")
    if not isinstance(maniskill_stats, dict):
        raise AssertionError("maniskill_proxy_stats.json must be a JSON object")
    require_keys(maniskill_stats, ["variant_summary", "comparisons"], context="maniskill_proxy_stats.json")
    if not isinstance(maniskill_stats["variant_summary"], dict):
        raise AssertionError("maniskill_proxy_stats.json.variant_summary must be an object")
    for required_variant in ("method", "ext2", "latency_aware", "adaptmanip"):
        if required_variant not in maniskill_stats["variant_summary"]:
            raise AssertionError(f"maniskill_proxy_stats.json.variant_summary missing {required_variant}")
    mani_cmp = maniskill_stats.get("comparisons")
    if not isinstance(mani_cmp, list) or not mani_cmp:
        raise AssertionError("maniskill_proxy_stats.json.comparisons must be non-empty")

    cross_embodiment = load_json(ROOT / "output/corepaper_reports/ws3/cross_embodiment_proxy_results.json")
    if not isinstance(cross_embodiment, dict):
        raise AssertionError("cross_embodiment_proxy_results.json must be a JSON object")
    require_keys(
        cross_embodiment,
        ["summary", "embodiment_breakdown", "episodes", "source_embodiment", "target_embodiments"],
        context="cross_embodiment_proxy_results.json",
    )
    if not isinstance(cross_embodiment["episodes"], list) or not cross_embodiment["episodes"]:
        raise AssertionError("cross_embodiment_proxy_results.json.episodes must be a non-empty list")
    if not isinstance(cross_embodiment["embodiment_breakdown"], list) or not cross_embodiment["embodiment_breakdown"]:
        raise AssertionError("cross_embodiment_proxy_results.json.embodiment_breakdown must be non-empty")

    cross_stats = load_json(ROOT / "output/corepaper_reports/ws3/cross_embodiment_proxy_stats.json")
    if not isinstance(cross_stats, dict):
        raise AssertionError("cross_embodiment_proxy_stats.json must be a JSON object")
    require_keys(
        cross_stats,
        ["variant_summary", "comparisons", "transfer_matrix", "source_embodiment"],
        context="cross_embodiment_proxy_stats.json",
    )
    if not isinstance(cross_stats["variant_summary"], dict):
        raise AssertionError("cross_embodiment_proxy_stats.json.variant_summary must be an object")
    for required_variant in ("method", "ext2", "latency_aware", "adaptmanip"):
        if required_variant not in cross_stats["variant_summary"]:
            raise AssertionError(f"cross_embodiment_proxy_stats.json.variant_summary missing {required_variant}")
    cross_cmp = cross_stats.get("comparisons")
    if not isinstance(cross_cmp, list) or not cross_cmp:
        raise AssertionError("cross_embodiment_proxy_stats.json.comparisons must be non-empty")
    transfer_matrix = cross_stats.get("transfer_matrix")
    if not isinstance(transfer_matrix, list) or not transfer_matrix:
        raise AssertionError("cross_embodiment_proxy_stats.json.transfer_matrix must be non-empty")

    library_lane = load_json(ROOT / "output/corepaper_reports/ws5/library_lane.json")
    if not isinstance(library_lane, dict):
        raise AssertionError("library_lane.json must be a JSON object")
    require_keys(
        library_lane,
        ["stress_aggregate", "comparisons"],
        context="library_lane.json",
    )
    stress_aggregate = library_lane.get("stress_aggregate")
    if not isinstance(stress_aggregate, dict):
        raise AssertionError("library_lane.json.stress_aggregate must be an object")
    for variant in ("method", "sb3_ppo", "rllib_sac"):
        row = stress_aggregate.get(variant)
        if not isinstance(row, dict):
            raise AssertionError(f"library_lane.json.stress_aggregate missing {variant}")
        for key in ("n", "mean", "worst", "cvar40"):
            if not _is_number(row.get(key)):
                raise AssertionError(f"Non-numeric {key} in library_lane.stress_aggregate[{variant}]")
    lib_comp = library_lane.get("comparisons")
    if not isinstance(lib_comp, list) or not lib_comp:
        raise AssertionError("library_lane.json.comparisons must be non-empty")
    for variant in ("sb3_ppo", "rllib_sac"):
        row = next(
            (
                item
                for item in lib_comp
                if isinstance(item, dict) and item.get("comparator_group") == variant
            ),
            None,
        )
        if row is None:
            raise AssertionError(f"library_lane.json.comparisons missing comparator_group={variant}")
        for key in ("delta_mean", "p_two_sided", "cohen_d"):
            if not _is_number(row.get(key)):
                raise AssertionError(f"Non-numeric {key} in library_lane comparison for {variant}")

    library_parity = load_json(ROOT / "output/corepaper_reports/ws5/library_parity_official.json")
    if not isinstance(library_parity, dict):
        raise AssertionError("library_parity_official.json must be a JSON object")
    require_keys(
        library_parity,
        ["repos", "local_mapping", "parity_summary"],
        context="library_parity_official.json",
    )
    repos = library_parity.get("repos")
    if not isinstance(repos, list) or len(repos) < 2:
        raise AssertionError("library_parity_official.json.repos must contain >= 2 rows")
    for row in repos:
        if not isinstance(row, dict):
            raise AssertionError("library_parity_official.json.repos row must be an object")
        require_keys(
            row,
            ["name", "head_commit", "source_file", "required_symbols", "symbol_hits", "status"],
            context="library_parity_official.json.repos[]",
        )
        if not isinstance(row.get("required_symbols"), list) or not row.get("required_symbols"):
            raise AssertionError("library_parity_official.json.repos[].required_symbols must be non-empty")
        if not isinstance(row.get("symbol_hits"), list) or not row.get("symbol_hits"):
            raise AssertionError("library_parity_official.json.repos[].symbol_hits must be non-empty")
        if str(row.get("status", "")).lower() not in {"pass", "fail"}:
            raise AssertionError("library_parity_official.json.repos[].status must be pass/fail")
    parity_summary = library_parity.get("parity_summary")
    if not isinstance(parity_summary, dict):
        raise AssertionError("library_parity_official.json.parity_summary must be an object")
    if str(parity_summary.get("overall_status", "")).lower() not in {"pass", "fail"}:
        raise AssertionError("library_parity_official.json.parity_summary.overall_status must be pass/fail")

    latency_parity = load_json(ROOT / "output/corepaper_reports/ws5/latency_aware_official_parity_audit.json")
    if not isinstance(latency_parity, dict):
        raise AssertionError("latency_aware_official_parity_audit.json must be a JSON object")
    require_keys(
        latency_parity,
        ["variant", "official_source", "subset_metrics", "parity_assessment"],
        context="latency_aware_official_parity_audit.json",
    )
    if str(latency_parity.get("variant", "")) != "latency_aware":
        raise AssertionError("latency_aware_official_parity_audit.json.variant must be latency_aware")
    subset = latency_parity.get("subset_metrics")
    if not isinstance(subset, dict):
        raise AssertionError("latency_aware_official_parity_audit.json.subset_metrics must be an object")
    for key in (
        "task_count",
        "n_rows_reference",
        "n_rows_comparator",
        "reference_mean",
        "comparator_mean",
        "delta_mean",
        "delta_worst_seed_mean",
        "delta_cvar40_seed",
    ):
        if key not in subset:
            raise AssertionError(f"latency_aware_official_parity_audit.json.subset_metrics missing {key}")
    if int(subset.get("task_count", 0)) < 3:
        raise AssertionError("latency_aware_official_parity_audit.json expected >=3 subset tasks")
    assessment = latency_parity.get("parity_assessment")
    if not isinstance(assessment, dict):
        raise AssertionError("latency_aware_official_parity_audit.json.parity_assessment must be an object")
    if not isinstance(assessment.get("status"), str) or not assessment.get("status"):
        raise AssertionError("latency_aware_official_parity_audit.json.parity_assessment.status must be non-empty")

    latency_n30 = load_json(ROOT / "output/corepaper_reports/ws3/metaworld_seedexp_latency_method_n30_stats.json")
    if not isinstance(latency_n30, dict):
        raise AssertionError("metaworld_seedexp_latency_method_n30_stats.json must be a JSON object")
    require_keys(
        latency_n30,
        ["variant_summary", "comparisons"],
        context="metaworld_seedexp_latency_method_n30_stats.json",
    )
    if not isinstance(latency_n30["variant_summary"], dict):
        raise AssertionError("metaworld_seedexp_latency_method_n30_stats.json.variant_summary must be an object")
    for variant in ("method", "latency_aware"):
        row = latency_n30["variant_summary"].get(variant)
        if not isinstance(row, dict):
            raise AssertionError(f"metaworld_seedexp_latency_method_n30_stats.json missing variant {variant}")
        if int(row.get("n_seeds", 0)) < 30:
            raise AssertionError(
                f"metaworld_seedexp_latency_method_n30_stats.json expected >=30 seeds for {variant}"
            )
    lat_comparisons = latency_n30.get("comparisons")
    if not isinstance(lat_comparisons, list) or not lat_comparisons:
        raise AssertionError("metaworld_seedexp_latency_method_n30_stats.json.comparisons must be non-empty")
    lat_row = next(
        (
            row
            for row in lat_comparisons
            if isinstance(row, dict) and row.get("comparator_group") == "latency_aware"
        ),
        None,
    )
    if lat_row is None:
        raise AssertionError("metaworld_seedexp_latency_method_n30_stats.json missing comparator_group=latency_aware")
    for key in ("delta_mean", "delta_worst_seed_mean", "delta_cvar40_seed", "p_two_sided"):
        if not _is_number(lat_row.get(key)):
            raise AssertionError(f"Non-numeric {key} in metaworld_seedexp_latency_method_n30 comparison row")

    adapt_n30 = load_json(ROOT / "output/corepaper_reports/ws3/metaworld_seedexp_adaptmanip_method_n30_stats.json")
    if not isinstance(adapt_n30, dict):
        raise AssertionError("metaworld_seedexp_adaptmanip_method_n30_stats.json must be a JSON object")
    require_keys(
        adapt_n30,
        ["variant_summary", "comparisons"],
        context="metaworld_seedexp_adaptmanip_method_n30_stats.json",
    )
    if not isinstance(adapt_n30["variant_summary"], dict):
        raise AssertionError("metaworld_seedexp_adaptmanip_method_n30_stats.json.variant_summary must be an object")
    for variant in ("method", "adaptmanip"):
        row = adapt_n30["variant_summary"].get(variant)
        if not isinstance(row, dict):
            raise AssertionError(f"metaworld_seedexp_adaptmanip_method_n30_stats.json missing variant {variant}")
        if int(row.get("n_seeds", 0)) < 30:
            raise AssertionError(
                f"metaworld_seedexp_adaptmanip_method_n30_stats.json expected >=30 seeds for {variant}"
            )
    adapt_comparisons = adapt_n30.get("comparisons")
    if not isinstance(adapt_comparisons, list) or not adapt_comparisons:
        raise AssertionError("metaworld_seedexp_adaptmanip_method_n30_stats.json.comparisons must be non-empty")
    adapt_row = next(
        (
            row
            for row in adapt_comparisons
            if isinstance(row, dict) and row.get("comparator_group") == "adaptmanip"
        ),
        None,
    )
    if adapt_row is None:
        raise AssertionError("metaworld_seedexp_adaptmanip_method_n30_stats.json missing comparator_group=adaptmanip")
    for key in ("delta_mean", "delta_worst_seed_mean", "delta_cvar40_seed", "p_two_sided"):
        if not _is_number(adapt_row.get(key)):
            raise AssertionError(f"Non-numeric {key} in metaworld_seedexp_adaptmanip_method_n30 comparison row")

    cvar_sens = load_json(ROOT / "output/corepaper_reports/ws5/metaworld_cvar_sensitivity_latency_n30.json")
    if not isinstance(cvar_sens, dict):
        raise AssertionError("metaworld_cvar_sensitivity_latency_n30.json must be a JSON object")
    require_keys(
        cvar_sens,
        ["reference_group", "comparator_group", "rows", "n_reference", "n_comparator"],
        context="metaworld_cvar_sensitivity_latency_n30.json",
    )
    if cvar_sens["reference_group"] != "method" or cvar_sens["comparator_group"] != "latency_aware":
        raise AssertionError("CVaR sensitivity report must compare method vs latency_aware")
    if int(cvar_sens["n_reference"]) < 30 or int(cvar_sens["n_comparator"]) < 30:
        raise AssertionError("CVaR sensitivity report expected >=30 seeds for both groups")
    sens_rows = cvar_sens["rows"]
    if not isinstance(sens_rows, list) or len(sens_rows) < 3:
        raise AssertionError("CVaR sensitivity report must include multiple alpha rows")
    for i, row in enumerate(sens_rows):
        if not isinstance(row, dict):
            raise AssertionError(f"CVaR sensitivity row {i} must be an object")
        require_keys(
            row,
            ["alpha", "reference_cvar", "comparator_cvar", "delta_cvar", "k_reference"],
            context=f"cvar_sensitivity.rows[{i}]",
        )
        for key in ("alpha", "reference_cvar", "comparator_cvar", "delta_cvar"):
            if not _is_number(row[key]):
                raise AssertionError(f"Non-numeric {key} in cvar_sensitivity.rows[{i}]")

    cvar_sens_adapt = load_json(ROOT / "output/corepaper_reports/ws5/metaworld_cvar_sensitivity_adaptmanip_n30.json")
    if not isinstance(cvar_sens_adapt, dict):
        raise AssertionError("metaworld_cvar_sensitivity_adaptmanip_n30.json must be a JSON object")
    require_keys(
        cvar_sens_adapt,
        ["reference_group", "comparator_group", "rows", "n_reference", "n_comparator"],
        context="metaworld_cvar_sensitivity_adaptmanip_n30.json",
    )
    if cvar_sens_adapt["reference_group"] != "method" or cvar_sens_adapt["comparator_group"] != "adaptmanip":
        raise AssertionError("CVaR sensitivity report must compare method vs adaptmanip")
    if int(cvar_sens_adapt["n_reference"]) < 30 or int(cvar_sens_adapt["n_comparator"]) < 30:
        raise AssertionError("Adaptmanip CVaR sensitivity report expected >=30 seeds for both groups")
    sens_rows_adapt = cvar_sens_adapt["rows"]
    if not isinstance(sens_rows_adapt, list) or len(sens_rows_adapt) < 3:
        raise AssertionError("Adaptmanip CVaR sensitivity report must include multiple alpha rows")
    for i, row in enumerate(sens_rows_adapt):
        if not isinstance(row, dict):
            raise AssertionError(f"Adaptmanip CVaR sensitivity row {i} must be an object")
        require_keys(
            row,
            ["alpha", "reference_cvar", "comparator_cvar", "delta_cvar", "k_reference"],
            context=f"cvar_sensitivity_adapt.rows[{i}]",
        )
        for key in ("alpha", "reference_cvar", "comparator_cvar", "delta_cvar"):
            if not _is_number(row[key]):
                raise AssertionError(f"Non-numeric {key} in cvar_sensitivity_adapt.rows[{i}]")

    adapt_equiv = load_json(ROOT / "output/corepaper_reports/ws5/metaworld_adapt_equivalence_n14.json")
    if not isinstance(adapt_equiv, dict):
        raise AssertionError("metaworld_adapt_equivalence_n14.json must be a JSON object")
    require_keys(
        adapt_equiv,
        [
            "reference_variant",
            "comparator_variant",
            "scenario",
            "n_shared_seeds",
            "equivalence_margin_abs",
            "metrics",
            "summary",
        ],
        context="metaworld_adapt_equivalence_n14.json",
    )
    if str(adapt_equiv.get("reference_variant", "")) != "method":
        raise AssertionError("metaworld_adapt_equivalence_n14.reference_variant must be method")
    if str(adapt_equiv.get("comparator_variant", "")) != "adaptmanip":
        raise AssertionError("metaworld_adapt_equivalence_n14.comparator_variant must be adaptmanip")
    if int(adapt_equiv.get("n_shared_seeds", 0)) < 10:
        raise AssertionError("metaworld_adapt_equivalence_n14 expected >=10 shared seeds")
    margin = float(adapt_equiv.get("equivalence_margin_abs", 0.0))
    if margin <= 0.0:
        raise AssertionError("metaworld_adapt_equivalence_n14 equivalence_margin_abs must be >0")
    eq_metrics = adapt_equiv.get("metrics")
    if not isinstance(eq_metrics, list) or len(eq_metrics) < 2:
        raise AssertionError("metaworld_adapt_equivalence_n14.metrics must include mean and cvar rows")
    for i, row in enumerate(eq_metrics):
        if not isinstance(row, dict):
            raise AssertionError(f"metaworld_adapt_equivalence_n14.metrics[{i}] must be an object")
        require_keys(
            row,
            [
                "metric",
                "observed_delta",
                "ci90_low",
                "ci90_high",
                "ci95_low",
                "ci95_high",
                "equivalence_supported",
            ],
            context=f"metaworld_adapt_equivalence_n14.metrics[{i}]",
        )
        for key in ("observed_delta", "ci90_low", "ci90_high", "ci95_low", "ci95_high"):
            if not _is_number(row.get(key)):
                raise AssertionError(f"Non-numeric {key} in metaworld_adapt_equivalence_n14.metrics[{i}]")
        if not isinstance(row.get("equivalence_supported"), bool):
            raise AssertionError(
                f"metaworld_adapt_equivalence_n14.metrics[{i}].equivalence_supported must be bool"
            )

    prop2_proxy = load_json(ROOT / "output/corepaper_reports/ws5/prop2_ordering_proxy.json")
    if not isinstance(prop2_proxy, dict):
        raise AssertionError("prop2_ordering_proxy.json must be a JSON object")
    require_keys(
        prop2_proxy,
        ["reference_variant", "comparators", "rows", "overall"],
        context="prop2_ordering_proxy.json",
    )
    if str(prop2_proxy.get("reference_variant", "")) != "method":
        raise AssertionError("prop2_ordering_proxy.json.reference_variant must be method")
    proxy_rows = prop2_proxy.get("rows")
    if not isinstance(proxy_rows, list) or not proxy_rows:
        raise AssertionError("prop2_ordering_proxy.json.rows must be non-empty")
    for i, row in enumerate(proxy_rows):
        if not isinstance(row, dict):
            raise AssertionError(f"prop2_ordering_proxy.rows[{i}] must be an object")
        require_keys(
            row,
            [
                "comparator",
                "paired_rows",
                "condition_holds_rate",
                "violation_rate",
                "mean_u_inc_minus_u_cand",
            ],
            context=f"prop2_ordering_proxy.rows[{i}]",
        )
        if int(row.get("paired_rows", 0)) < 10:
            raise AssertionError("prop2_ordering_proxy expected >=10 paired rows per comparator")
        for key in ("condition_holds_rate", "violation_rate", "mean_u_inc_minus_u_cand"):
            if not _is_number(row.get(key)):
                raise AssertionError(f"Non-numeric {key} in prop2_ordering_proxy.rows[{i}]")

    budget_parity = load_json(ROOT / "output/corepaper_reports/ws5/metaworld_budget_parity.json")
    if not isinstance(budget_parity, dict):
        raise AssertionError("metaworld_budget_parity.json must be a JSON object")
    require_keys(
        budget_parity,
        ["reference_variant", "rows", "summary"],
        context="metaworld_budget_parity.json",
    )
    if str(budget_parity.get("reference_variant", "")) != "method":
        raise AssertionError("metaworld_budget_parity.json.reference_variant must be method")
    budget_rows = budget_parity.get("rows")
    if not isinstance(budget_rows, list) or len(budget_rows) < 2:
        raise AssertionError("metaworld_budget_parity.json.rows must include >=2 comparator rows")
    for i, row in enumerate(budget_rows):
        if not isinstance(row, dict):
            raise AssertionError(f"metaworld_budget_parity.rows[{i}] must be an object")
        require_keys(
            row,
            [
                "suite_name",
                "comparator",
                "max_steps_per_episode",
                "extra_monitor_episodes",
                "delta_episodes",
                "delta_total_steps",
            ],
            context=f"metaworld_budget_parity.rows[{i}]",
        )
        if int(row.get("max_steps_per_episode", 0)) <= 0:
            raise AssertionError("metaworld_budget_parity.max_steps_per_episode must be >0")
        if int(row.get("extra_monitor_episodes", -1)) < 0:
            raise AssertionError("metaworld_budget_parity.extra_monitor_episodes must be >=0")
        for key in ("delta_total_steps", "delta_mean_steps"):
            if not _is_number(row.get(key)):
                raise AssertionError(f"Non-numeric {key} in metaworld_budget_parity.rows[{i}]")

    theorem1_neff = load_json(ROOT / "output/corepaper_reports/ws5/theorem1_neff_diagnostic.json")
    if not isinstance(theorem1_neff, dict):
        raise AssertionError("theorem1_neff_diagnostic.json must be a JSON object")
    require_keys(
        theorem1_neff,
        ["reference_variant", "scenario", "rows", "summary"],
        context="theorem1_neff_diagnostic.json",
    )
    if str(theorem1_neff.get("reference_variant", "")) != "method":
        raise AssertionError("theorem1_neff_diagnostic.json.reference_variant must be method")
    neff_rows = theorem1_neff.get("rows")
    if not isinstance(neff_rows, list) or len(neff_rows) < 1:
        raise AssertionError("theorem1_neff_diagnostic.json.rows must be non-empty")
    for i, row in enumerate(neff_rows):
        if not isinstance(row, dict):
            raise AssertionError(f"theorem1_neff_diagnostic.rows[{i}] must be an object")
        require_keys(
            row,
            [
                "suite_name",
                "comparator",
                "paired_rows",
                "icc_seed_cluster",
                "design_effect",
                "n_eff_estimate",
            ],
            context=f"theorem1_neff_diagnostic.rows[{i}]",
        )
        if int(row.get("paired_rows", 0)) < 20:
            raise AssertionError("theorem1_neff_diagnostic expected >=20 paired rows")
        for key in ("icc_seed_cluster", "design_effect", "n_eff_estimate"):
            if not _is_number(row.get(key)):
                raise AssertionError(f"Non-numeric {key} in theorem1_neff_diagnostic.rows[{i}]")
        if float(row.get("design_effect", 0.0)) < 1.0:
            raise AssertionError("theorem1_neff_diagnostic.design_effect must be >=1")

    misspec = load_json(ROOT / "output/corepaper_reports/ws5/uncertainty_misspec_sensitivity.json")
    if not isinstance(misspec, dict):
        raise AssertionError("uncertainty_misspec_sensitivity.json must be a JSON object")
    require_keys(
        misspec,
        ["base_fit", "grid", "summary", "rows", "holdout_rows"],
        context="uncertainty_misspec_sensitivity.json",
    )
    base_fit = misspec.get("base_fit")
    if not isinstance(base_fit, dict):
        raise AssertionError("uncertainty_misspec_sensitivity.json.base_fit must be an object")
    for key in ("c_u", "c_0", "accept_rate"):
        if not _is_number(base_fit.get(key)):
            raise AssertionError(f"Non-numeric {key} in uncertainty_misspec_sensitivity.base_fit")
    if int(misspec.get("holdout_rows", 0)) < 20:
        raise AssertionError("uncertainty_misspec_sensitivity expected >=20 holdout rows")
    grid = misspec.get("grid")
    if not isinstance(grid, dict):
        raise AssertionError("uncertainty_misspec_sensitivity.json.grid must be an object")
    for key in ("cu_scales", "c0_shifts"):
        vals = grid.get(key)
        if not isinstance(vals, list) or len(vals) < 3:
            raise AssertionError(f"uncertainty_misspec_sensitivity.grid.{key} must include >=3 values")
    rows = misspec.get("rows")
    if not isinstance(rows, list) or not rows:
        raise AssertionError("uncertainty_misspec_sensitivity.json.rows must be non-empty")
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            raise AssertionError(f"uncertainty_misspec_sensitivity row {i} must be an object")
        require_keys(
            row,
            [
                "cu_scale",
                "c0_shift",
                "c_u",
                "c_0",
                "decision_agreement_vs_base",
                "false_accept_vs_base_rate",
                "false_reject_vs_base_rate",
            ],
            context=f"uncertainty_misspec_sensitivity.rows[{i}]",
        )
        for key in (
            "cu_scale",
            "c0_shift",
            "c_u",
            "c_0",
            "decision_agreement_vs_base",
            "false_accept_vs_base_rate",
            "false_reject_vs_base_rate",
        ):
            if not _is_number(row.get(key)):
                raise AssertionError(f"Non-numeric {key} in uncertainty_misspec_sensitivity.rows[{i}]")

    o2o_recent = load_json(ROOT / "output/corepaper_reports/ws5/o2o_proxy_recent.json")
    if not isinstance(o2o_recent, dict):
        raise AssertionError("o2o_proxy_recent.json must be a JSON object")
    require_keys(o2o_recent, ["stress_aggregate", "comparisons"], context="o2o_proxy_recent.json")
    if not isinstance(o2o_recent["stress_aggregate"], dict) or not o2o_recent["stress_aggregate"]:
        raise AssertionError("o2o_proxy_recent.json.stress_aggregate must be non-empty")
    if "method" not in o2o_recent["stress_aggregate"] or "ext2" not in o2o_recent["stress_aggregate"]:
        raise AssertionError("o2o_proxy_recent.json.stress_aggregate must include method and ext2")
    if not isinstance(o2o_recent["comparisons"], list) or not o2o_recent["comparisons"]:
        raise AssertionError("o2o_proxy_recent.json.comparisons must be non-empty")
    if not any(
        isinstance(row, dict) and row.get("comparator_group") == "ext2"
        for row in o2o_recent["comparisons"]
    ):
        raise AssertionError("o2o_proxy_recent.json.comparisons missing ext2 comparator")

    o2o_fail = load_json(ROOT / "output/corepaper_reports/ws5/o2o_failure_accounting.json")
    if not isinstance(o2o_fail, dict):
        raise AssertionError("o2o_failure_accounting.json must be a JSON object")
    require_keys(o2o_fail, ["summary", "comparisons", "reference_group"], context="o2o_failure_accounting.json")
    if not isinstance(o2o_fail["summary"], dict) or "method" not in o2o_fail["summary"]:
        raise AssertionError("o2o_failure_accounting.json.summary must include method")
    summary_method = o2o_fail["summary"]["method"]
    for key in ("mean_online", "mean_offline", "mean_gain", "mean_interventions", "mean_catastrophic_events"):
        if not _is_number(summary_method.get(key)):
            raise AssertionError(f"Non-numeric {key} in o2o_failure_accounting.summary.method")

    verification = load_json(ROOT / "output/corepaper_reports/ws5/verification_first_diagnostics.json")
    if not isinstance(verification, dict):
        raise AssertionError("verification_first_diagnostics.json must be a JSON object")
    require_keys(
        verification,
        ["rows", "failure_taxonomy", "summary", "verification_scaling"],
        context="verification_first_diagnostics.json",
    )
    if not isinstance(verification["rows"], list) or not verification["rows"]:
        raise AssertionError("verification_first_diagnostics.json.rows must be non-empty")
    method_row = next(
        (
            row
            for row in verification["rows"]
            if isinstance(row, dict) and row.get("variant") == "method"
        ),
        None,
    )
    if method_row is None:
        raise AssertionError("verification_first_diagnostics.json missing method row")
    for key in ("pass_count", "fail_count", "pass_ratio"):
        if not _is_number(method_row.get(key)):
            raise AssertionError(f"Non-numeric {key} in verification_first_diagnostics.method row")

    adversarial = load_json(ROOT / "output/corepaper_reports/ws5/adversarial_stress_results.json")
    if not isinstance(adversarial, dict):
        raise AssertionError("adversarial_stress_results.json must be a JSON object")
    require_keys(
        adversarial,
        ["stress_aggregate", "comparisons", "coverage_matrix", "scenario_components"],
        context="adversarial_stress_results.json",
    )
    if not isinstance(adversarial["stress_aggregate"], dict) or "method" not in adversarial["stress_aggregate"]:
        raise AssertionError("adversarial_stress_results.json.stress_aggregate must include method")
    adv_cmp = adversarial.get("comparisons")
    if not isinstance(adv_cmp, list) or not adv_cmp:
        raise AssertionError("adversarial_stress_results.json.comparisons must be non-empty")
    if not any(isinstance(row, dict) and row.get("comparator_group") == "ext2" for row in adv_cmp):
        raise AssertionError("adversarial_stress_results.json.comparisons missing ext2 comparator")
    coverage = adversarial.get("coverage_matrix")
    if not isinstance(coverage, dict) or not coverage:
        raise AssertionError("adversarial_stress_results.json.coverage_matrix must be non-empty")

    effects = load_json(ROOT / "output/corepaper_reports/ws5/statistical_effects.json")
    if not isinstance(effects, dict):
        raise AssertionError("statistical_effects.json must be a JSON object")
    effect_rows = effects.get("rows")
    if not isinstance(effect_rows, list):
        raise AssertionError("statistical_effects.json.rows must be a list")
    if not any(isinstance(r, dict) and r.get("comparator_group") == "ext2" for r in effect_rows):
        raise AssertionError("statistical_effects.json.rows must include comparator_group=ext2")

    effects_n14 = load_json(ROOT / "output/corepaper_reports/ws5/corepaper_external_n14_statistical_effects.json")
    if not isinstance(effects_n14, dict):
        raise AssertionError("corepaper_external_n14_statistical_effects.json must be a JSON object")
    rows_n14 = effects_n14.get("rows")
    if not isinstance(rows_n14, list):
        raise AssertionError("corepaper_external_n14_statistical_effects.json.rows must be a list")
    ext2_row = next(
        (
            row
            for row in rows_n14
            if isinstance(row, dict) and row.get("comparator_group") == "ext2"
        ),
        None,
    )
    if ext2_row is None:
        raise AssertionError("corepaper_external_n14_statistical_effects.json.rows missing comparator_group=ext2")
    for key in ("delta_mean", "delta_ci95_halfwidth", "p_two_sided"):
        if not _is_number(ext2_row.get(key)):
            raise AssertionError(f"Non-numeric {key} in n14 ext2 comparison row")
    for key in ("n_reference", "n_comparator"):
        if not isinstance(ext2_row.get(key), int) or int(ext2_row[key]) < 10:
            raise AssertionError(f"Expected >=10 for {key} in n14 ext2 comparison row")

    reliability = load_json(ROOT / "output/corepaper_reports/ws5/reliability_floor.json")
    if not isinstance(reliability, dict):
        raise AssertionError("reliability_floor.json must be a JSON object")
    require_keys(reliability, ["reference", "comparator", "bins"], context="reliability_floor.json")
    bins = reliability["bins"]
    if not isinstance(bins, list) or len(bins) < 2:
        raise AssertionError("reliability_floor.json.bins must contain at least two bins")
    if not isinstance(reliability["reference"], dict) or not isinstance(reliability["comparator"], dict):
        raise AssertionError("reliability_floor reference/comparator must be objects")
    for side in ("reference", "comparator"):
        require_keys(reliability[side], ["name", "mean", "worst", "cvar40", "failure_tail_rate"], context=side)
        if not isinstance(reliability[side]["name"], str) or not reliability[side]["name"]:
            raise AssertionError(f"Invalid name in reliability_floor.{side}")
        for k in ("mean", "worst", "cvar40", "failure_tail_rate"):
            if not _is_number(reliability[side][k]):
                raise AssertionError(f"Non-numeric {k} in reliability_floor.{side}")

    reliability_n14 = load_json(ROOT / "output/corepaper_reports/ws5/corepaper_reliability_floor_n14.json")
    if not isinstance(reliability_n14, dict):
        raise AssertionError("corepaper_reliability_floor_n14.json must be a JSON object")
    require_keys(reliability_n14, ["reference", "comparator", "bins"], context="corepaper_reliability_floor_n14.json")
    for side, expected_name in (("reference", "method"), ("comparator", "ext2")):
        if not isinstance(reliability_n14[side], dict):
            raise AssertionError(f"corepaper_reliability_floor_n14.{side} must be an object")
        require_keys(
            reliability_n14[side],
            ["name", "values", "mean", "worst", "cvar40", "failure_tail_rate"],
            context=f"corepaper_reliability_floor_n14.{side}",
        )
        if reliability_n14[side]["name"] != expected_name:
            raise AssertionError(
                f"corepaper_reliability_floor_n14.{side}.name expected {expected_name!r}"
            )
        values = reliability_n14[side]["values"]
        if not isinstance(values, list) or len(values) < 10:
            raise AssertionError(
                f"corepaper_reliability_floor_n14.{side}.values must include >=10 entries"
            )
        for k in ("mean", "worst", "cvar40", "failure_tail_rate"):
            if not _is_number(reliability_n14[side][k]):
                raise AssertionError(f"Non-numeric {k} in corepaper_reliability_floor_n14.{side}")

    sim2sim = load_json(ROOT / "output/corepaper_reports/ws5/sim2sim_transfer_results.json")
    if not isinstance(sim2sim, dict):
        raise AssertionError("sim2sim_transfer_results.json must be a JSON object")
    require_keys(sim2sim, ["rows", "criteria", "all_required_pass"], context="sim2sim_transfer_results.json")
    sim_rows = sim2sim["rows"]
    if not isinstance(sim_rows, list) or not sim_rows:
        raise AssertionError("sim2sim_transfer_results.json.rows must be a non-empty list")
    first = sim_rows[0]
    if not isinstance(first, dict):
        raise AssertionError("sim2sim_transfer_results.json.rows[0] must be an object")
    require_keys(
        first,
        ["engine", "method_mean", "baseline_mean", "method_minus_baseline", "method_beats_baseline"],
        context="sim2sim_transfer_results.json.rows[0]",
    )
    if not isinstance(first["method_beats_baseline"], bool):
        raise AssertionError("sim2sim method_beats_baseline must be bool")
    for k in ("method_mean", "baseline_mean", "method_minus_baseline"):
        if first[k] is not None and not _is_number(first[k]):
            raise AssertionError(f"Non-numeric {k} in sim2sim row")

    macros_text = (ROOT / "paper/generated/results_macros.tex").read_text(encoding="utf-8")
    for macro in (
        "CoreRepoVersion",
        "CoreCvarAlpha",
        "CoreSeedExpN",
        "CoreFullNFourteenMethodMean",
        "CoreMetaSeedExpLatencyN",
        "CoreMetaSeedExpLatencyNThirtyN",
        "CoreMetaLatencyCvarAlphaMinDelta",
        "CoreCalibrationMaxAbsError",
        "CoreLibLaneN",
        "CoreLibLaneDeltaSbThree",
        "CoreLibLaneDeltaRllib",
        "CoreMetaAdaptEqBothLabel",
        "CoreMetaSeedExpAdaptNThirtyPermMcSeMean",
        "CoreMetaSeedExpAdaptNThirtyPermMcSeCvar",
    ):
        if f"\\providecommand{{\\{macro}}}" not in macros_text:
            raise AssertionError(f"Missing macro in results_macros.tex: {macro}")
    if "nan" in macros_text.lower():
        raise AssertionError("Detected 'nan' token in results_macros.tex")
    if "closest-comparator parity" in macros_text:
        raise AssertionError("results_macros.tex contains deprecated 'closest-comparator parity' phrasing")

    paper_text = (ROOT / "paper/manuscript.tex").read_text(encoding="utf-8")
    provided_core_macros = set(re.findall(r"\\providecommand\{\\(Core[A-Za-z0-9]+)\}", macros_text))
    local_core_macros = set(re.findall(r"\\newcommand\{\\(Core[A-Za-z0-9]+)\}", paper_text))
    used_core_macros = set(re.findall(r"\\(Core[A-Za-z0-9]+)", paper_text))
    unresolved_core = sorted(
        name for name in used_core_macros if name not in provided_core_macros and name not in local_core_macros
    )
    if unresolved_core:
        sample = ", ".join(unresolved_core[:12])
        raise AssertionError(
            "manuscript.tex references undefined Core* macros (first 12): "
            f"{sample}"
        )
    for banned in ("p =<", "0.000100and", "diagnostic certificate", "certified lower-bound proxy"):
        if banned in paper_text:
            raise AssertionError(f"manuscript.tex contains banned token: {banned}")
    if "\\usepackage{censor}" not in paper_text:
        raise AssertionError("manuscript.tex must include \\usepackage{censor} for double-anonymous redaction")
    if "\\doubleanonymousreviewtrue" not in paper_text:
        raise AssertionError("manuscript.tex must enable double-anonymous mode by default")
    for ack_heading in (
        "\\section*{Acknowledgments}",
        "\\section*{Acknowledgements}",
        "\\section{Acknowledgments}",
        "\\section{Acknowledgements}",
    ):
        if ack_heading in paper_text:
            raise AssertionError(f"manuscript.tex contains non-anonymous section heading: {ack_heading}")

    snapshot = load_json(ROOT / "output/corepaper_reports/version_snapshot.json")
    if not isinstance(snapshot, dict):
        raise AssertionError("version_snapshot.json must be a JSON object")
    require_keys(snapshot, ["version", "generated_at_utc", "artifacts"], context="version_snapshot.json")
    if not isinstance(snapshot["version"], str) or not snapshot["version"]:
        raise AssertionError("version_snapshot.json.version must be a non-empty string")
    if not isinstance(snapshot["artifacts"], list) or not snapshot["artifacts"]:
        raise AssertionError("version_snapshot.json.artifacts must be a non-empty list")


def _check_pdf_body_page_limit(*, max_body_pages: int = 6, max_words_before_references: int = 80) -> None:
    pdf = ROOT / "paper/build/manuscript.pdf"
    require_file(pdf, min_size=100_000)
    require_file_max(pdf, max_size=6 * 1024 * 1024)

    try:
        info = subprocess.check_output(["pdfinfo", str(pdf)], text=True, stderr=subprocess.STDOUT)
    except FileNotFoundError as exc:
        raise AssertionError("Missing required tool: pdfinfo") from exc
    except subprocess.CalledProcessError as exc:
        raise AssertionError(f"pdfinfo failed for {pdf}: {exc.output.strip()}") from exc

    match = re.search(r"^Pages:\s+(\d+)\s*$", info, flags=re.MULTILINE)
    if match is None:
        raise AssertionError("Could not parse PDF page count from pdfinfo output")
    page_count = int(match.group(1))
    if page_count <= 0:
        raise AssertionError("Invalid PDF page count")

    author_match = re.search(r"^Author:\s*(.*)$", info, flags=re.MULTILINE)
    if author_match:
        author_value = author_match.group(1).strip()
        if author_value and "anonymous" not in author_value.lower():
            raise AssertionError(f"PDF metadata Author field must be anonymous; found: {author_value!r}")

    ref_page = None
    words_before_ref = 0
    ref_pattern = re.compile(
        r"(?mi)^\s*R\s*E\s*F\s*E\s*R\s*E\s*N\s*C\s*E\s*S\b"
    )

    for page in range(1, page_count + 1):
        try:
            text = subprocess.check_output(
                ["pdftotext", "-f", str(page), "-l", str(page), str(pdf), "-"],
                text=True,
                stderr=subprocess.STDOUT,
            )
        except FileNotFoundError as exc:
            raise AssertionError("Missing required tool: pdftotext") from exc
        except subprocess.CalledProcessError as exc:
            raise AssertionError(f"pdftotext failed on page {page}: {exc.output.strip()}") from exc

        ref_match = ref_pattern.search(text)
        if ref_match is None:
            continue
        ref_page = page
        words_before_ref = len(re.findall(r"[A-Za-z0-9_]+", text[: ref_match.start()]))
        break

    if ref_page is None:
        raise AssertionError("Could not locate REFERENCES heading in paper/build/manuscript.pdf")

    body_pages_before_ref = ref_page - 1
    if body_pages_before_ref > max_body_pages:
        raise AssertionError(
            f"Body exceeds {max_body_pages}-page limit: references start on page {ref_page}"
        )
    if body_pages_before_ref == max_body_pages and words_before_ref > max_words_before_references:
        raise AssertionError(
            "Body exceeds strict limit: references start too late on page "
            f"{ref_page} ({words_before_ref} words before REFERENCES)"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--label",
        default="pipeline",
        help="Human-readable run label for logs.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    _check_required_artifacts()
    _check_json_shapes()
    _check_pdf_body_page_limit()
    print(f"[{args.label}] pipeline sanity checks passed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"Pipeline sanity check failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
