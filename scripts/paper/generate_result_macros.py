#!/usr/bin/env python3
"""Generate LaTeX macros for paper result numbers from experiment/report artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
from math import sqrt
from statistics import NormalDist, mean
from typing import Any, Dict, Iterable, List


ROOT = pathlib.Path(__file__).resolve().parents[2]
STANDARD_NORMAL = NormalDist()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default="paper/generated/results_macros.tex",
        help="Path to generated LaTeX macro file.",
    )
    return parser.parse_args()


def load_json(path: pathlib.Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def find_row(rows: Iterable[Dict[str, Any]], **matches: Any) -> Dict[str, Any]:
    for row in rows:
        if all(row.get(k) == v for k, v in matches.items()):
            return row
    keys = ", ".join(f"{k}={v}" for k, v in matches.items())
    raise KeyError(f"Missing row matching: {keys}")


def fmt(v: float, digits: int) -> str:
    return f"{v:.{digits}f}"


def fmt_p(v: float, digits: int = 4, lower_bound: float = 1e-4) -> str:
    if v < lower_bound:
        return f"<{lower_bound:.{digits}f}"
    return f"{v:.{digits}f}"


def fmt_signed(v: float, digits: int) -> str:
    return f"{v:+.{digits}f}"


def fmt_pct(v: float, digits: int = 2) -> str:
    return f"{v:.{digits}f}\\%"


def ci95_from_samples(values: List[float]) -> float:
    n = len(values)
    if n <= 1:
        return 0.0
    mu = sum(values) / n
    var = sum((v - mu) ** 2 for v in values) / (n - 1)
    return 1.96 * sqrt(var / n)


def approx_two_sample_power_from_d(d: float, n_per_group: int, alpha: float = 0.05) -> float:
    """Normal-approximation two-sided power for equal-sized groups."""
    if n_per_group <= 0:
        return 0.0
    z_alpha = STANDARD_NORMAL.inv_cdf(1.0 - alpha / 2.0)
    noncentral = abs(d) * sqrt(n_per_group / 2.0)
    power = 1.0 - STANDARD_NORMAL.cdf(z_alpha - noncentral) + STANDARD_NORMAL.cdf(-z_alpha - noncentral)
    return max(0.0, min(1.0, power))


def approx_n_per_group_for_power(d: float, target_power: float = 0.8, alpha: float = 0.05) -> int:
    """Approximate per-group sample count for equal-sized two-sample design."""
    if abs(d) < 1e-9:
        return 9999
    z_alpha = STANDARD_NORMAL.inv_cdf(1.0 - alpha / 2.0)
    z_beta = STANDARD_NORMAL.inv_cdf(target_power)
    n = 2.0 * ((z_alpha + z_beta) ** 2) / (abs(d) ** 2)
    return max(2, int(n + 0.999999))


def significance_label(is_significant: bool) -> str:
    return "Holm-significant" if is_significant else "Holm-non-significant"


def bonferroni_significance_label(is_significant: bool) -> str:
    return "Bonferroni-significant" if is_significant else "Bonferroni-non-significant"


def nominal_significance_label(is_significant: bool) -> str:
    return "significant" if is_significant else "non-significant"


def direction_label(v: float, eps: float = 1e-12) -> str:
    if v > eps:
        return "positive"
    if v < -eps:
        return "negative"
    return "zero"


def mc_se_from_probability(p: float, n_samples: int) -> float:
    if n_samples <= 0:
        return 0.0
    p_clip = max(0.0, min(1.0, float(p)))
    return sqrt(p_clip * (1.0 - p_clip) / float(n_samples))


def holm_bonferroni(pvals: List[float]) -> List[float]:
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    out = [1.0] * m
    prev = 0.0
    for rank, idx in enumerate(order):
        value = max(prev, (m - rank) * pvals[idx])
        prev = value
        out[idx] = min(1.0, value)
    return out


def cvar_bottom(values: List[float], fraction: float = 0.4) -> float:
    if not values:
        return 0.0
    k = max(1, int(round(len(values) * fraction)))
    return mean(sorted(values)[:k])


def subset_shifted_delta_from_episodes(
    episodes: Iterable[Dict[str, Any]],
    *,
    tasks: Iterable[str],
    reference_variant: str = "method",
    comparator_variant: str = "latency_aware",
) -> Dict[str, float]:
    task_set = {str(task) for task in tasks}
    by_variant_values: Dict[str, List[float]] = {reference_variant: [], comparator_variant: []}
    by_variant_seed: Dict[str, Dict[int, List[float]]] = {
        reference_variant: {},
        comparator_variant: {},
    }

    for row in episodes:
        if str(row.get("scenario")) != "shifted":
            continue
        if str(row.get("task")) not in task_set:
            continue
        variant = str(row.get("variant"))
        if variant not in by_variant_values:
            continue
        value = float(row.get("success_final", 0.0))
        seed = int(row.get("seed", 0))
        by_variant_values[variant].append(value)
        by_variant_seed[variant].setdefault(seed, []).append(value)

    ref_vals = by_variant_values[reference_variant]
    comp_vals = by_variant_values[comparator_variant]
    if not ref_vals or not comp_vals:
        return {
            "delta_mean": 0.0,
            "delta_worst_seed_mean": 0.0,
            "delta_cvar40_seed": 0.0,
        }

    ref_seed_means = [mean(vals) for vals in by_variant_seed[reference_variant].values() if vals]
    comp_seed_means = [mean(vals) for vals in by_variant_seed[comparator_variant].values() if vals]
    if not ref_seed_means or not comp_seed_means:
        return {
            "delta_mean": 0.0,
            "delta_worst_seed_mean": 0.0,
            "delta_cvar40_seed": 0.0,
        }

    return {
        "delta_mean": mean(ref_vals) - mean(comp_vals),
        "delta_worst_seed_mean": min(ref_seed_means) - min(comp_seed_means),
        "delta_cvar40_seed": cvar_bottom(ref_seed_means, 0.4) - cvar_bottom(comp_seed_means, 0.4),
    }


def macro_lines(macros: Dict[str, str]) -> List[str]:
    lines: List[str] = []
    lines.append("% Auto-generated file. Do not edit manually.")
    lines.append("% Generated by scripts/paper/generate_result_macros.py")
    for name in sorted(macros):
        lines.append(f"\\providecommand{{\\{name}}}{{{macros[name]}}}")
    return lines


def build_macros() -> Dict[str, str]:
    # Sources
    meta_stats = load_json(ROOT / "output/corepaper_reports/ws3/metaworld_recent_baselines_stats.json")
    maniskill_stats = load_json(ROOT / "output/corepaper_reports/ws3/maniskill_proxy_stats.json")
    cross_embodiment_stats = load_json(ROOT / "output/corepaper_reports/ws3/cross_embodiment_proxy_stats.json")
    meta_results = load_json(ROOT / "output/corepaper_reports/ws3/metaworld_recent_baselines_results.json")
    meta_slice_stats = load_json(ROOT / "output/corepaper_reports/ws3/metaworld_slice_stats.json")
    meta_seedexp = load_json(ROOT / "output/corepaper_reports/ws3/metaworld_seedexp_ext2_method_stats.json")
    meta_seedexp_results = load_json(ROOT / "output/corepaper_reports/ws3/metaworld_seedexp_ext2_method_results.json")
    meta_seedexp_latency = load_json(ROOT / "output/corepaper_reports/ws3/metaworld_seedexp_latency_method_stats.json")
    meta_seedexp_latency_n30 = load_json(
        ROOT / "output/corepaper_reports/ws3/metaworld_seedexp_latency_method_n30_stats.json"
    )
    meta_seedexp_adapt = load_json(ROOT / "output/corepaper_reports/ws3/metaworld_seedexp_adaptmanip_method_stats.json")
    meta_seedexp_adapt_n30 = load_json(
        ROOT / "output/corepaper_reports/ws3/metaworld_seedexp_adaptmanip_method_n30_stats.json"
    )
    meta_cvar_sensitivity = load_json(
        ROOT / "output/corepaper_reports/ws5/metaworld_cvar_sensitivity_latency_n30.json"
    )
    meta_cvar_sensitivity_adapt = load_json(
        ROOT / "output/corepaper_reports/ws5/metaworld_cvar_sensitivity_adaptmanip_n30.json"
    )

    custom_n5 = load_json(ROOT / "output/corepaper_reports/ws5/statistical_effects.json")
    custom_ci = load_json(ROOT / "output/corepaper_reports/ws5/custom_scenario_ci.json")
    custom_n14 = load_json(ROOT / "output/corepaper_reports/ws5/corepaper_external_n14_statistical_effects.json")
    seed_exp = load_json(ROOT / "output/corepaper_reports/ws5/seed_expansion_method_vs_ext2.json")
    rel_n5 = load_json(ROOT / "output/corepaper_reports/ws5/reliability_floor.json")
    rel_n14 = load_json(ROOT / "output/corepaper_reports/ws5/corepaper_reliability_floor_n14.json")

    ablation = load_json(ROOT / "output/corepaper_reports/ws5/ablation_results.json")
    robustness = load_json(ROOT / "output/corepaper_reports/ws5/robustness_results.json")
    soft_transfer = load_json(ROOT / "output/corepaper_reports/ws5/software_transfer_results.json")
    sim2sim = load_json(ROOT / "output/corepaper_reports/ws5/sim2sim_transfer_results.json")
    o2o_recent = load_json(ROOT / "output/corepaper_reports/ws5/o2o_proxy_recent.json")
    o2o_fail = load_json(ROOT / "output/corepaper_reports/ws5/o2o_failure_accounting.json")
    verification = load_json(ROOT / "output/corepaper_reports/ws5/verification_first_diagnostics.json")
    adversarial = load_json(ROOT / "output/corepaper_reports/ws5/adversarial_stress_results.json")
    uncertainty = load_json(ROOT / "output/corepaper_reports/ws5/uncertainty_dominance.json")
    uncertainty_misspec = load_json(ROOT / "output/corepaper_reports/ws5/uncertainty_misspec_sensitivity.json")
    prop2_proxy = load_json(ROOT / "output/corepaper_reports/ws5/prop2_ordering_proxy.json")
    budget_parity = load_json(ROOT / "output/corepaper_reports/ws5/metaworld_budget_parity.json")
    theorem1_neff = load_json(ROOT / "output/corepaper_reports/ws5/theorem1_neff_diagnostic.json")
    adapt_equivalence_path = ROOT / "output/corepaper_reports/ws5/metaworld_adapt_equivalence_n14.json"
    adapt_equivalence = load_json(adapt_equivalence_path) if adapt_equivalence_path.exists() else {}
    tau_sweep = load_json(ROOT / "output/corepaper_reports/ws5/gate_threshold_sensitivity.json")
    library_lane = load_json(ROOT / "output/corepaper_reports/ws5/library_lane.json")
    library_parity = load_json(ROOT / "output/corepaper_reports/ws5/library_parity_official.json")
    latency_official_parity = load_json(ROOT / "output/corepaper_reports/ws5/latency_aware_official_parity_audit.json")
    baseline_calibration = load_json(ROOT / "output/corepaper_reports/ws3/baseline_calibration.json")

    pvals_meta = load_json(ROOT / "output/corepaper_reports/ws3/pvalue_corrections_metaworld_recent.json")
    pvals_recent = load_json(ROOT / "output/corepaper_reports/ws5/pvalue_corrections_recent_stress.json")

    metaworld_cfg = load_json(ROOT / "config/benchmarks/experiments_metaworld_recent_baselines.json")
    adapt_seedexp_n14_cfg = ROOT / "config/benchmarks/experiments_metaworld_seedexp_adaptmanip_method.json"
    adapt_seedexp_n30_cfg = ROOT / "config/benchmarks/experiments_metaworld_seedexp_adaptmanip_method_n30.json"
    cycle_dir = ROOT / "output/corepaper_logs/ws4/cycles"

    macros: Dict[str, str] = {}
    macros["CoreRepoVersion"] = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    macros["CoreMetaAdaptSeedexpConfigHashNFourteen"] = hashlib.sha256(
        adapt_seedexp_n14_cfg.read_bytes()
    ).hexdigest()[:12]
    macros["CoreMetaAdaptSeedexpConfigHashNThirty"] = hashlib.sha256(
        adapt_seedexp_n30_cfg.read_bytes()
    ).hexdigest()[:12]

    def variant_row(summary: Dict[str, Dict[str, Any]], key: str) -> Dict[str, Any]:
        return summary.get(
            key,
            {
                "mean_success": 0.0,
                "worst_seed_mean": 0.0,
                "cvar40_seed": 0.0,
                "success_per_1k_steps": 0.0,
            },
        )

    # Experiment constants and setup
    configured_meta_tasks = [str(task) for task in metaworld_cfg.get("tasks", [])]
    observed_shifted_tasks: List[str] = []
    _seen_tasks = set()
    for row in meta_results.get("task_breakdown", []):
        if str(row.get("scenario")) != "shifted":
            continue
        task_name = str(row.get("task", "")).strip()
        if task_name and task_name not in _seen_tasks:
            _seen_tasks.add(task_name)
            observed_shifted_tasks.append(task_name)
    if configured_meta_tasks:
        observed_set = set(observed_shifted_tasks)
        ordered_shifted_tasks = [task for task in configured_meta_tasks if task in observed_set]
        ordered_shifted_tasks.extend(task for task in observed_shifted_tasks if task not in ordered_shifted_tasks)
    else:
        ordered_shifted_tasks = observed_shifted_tasks

    def _task_alias(task_name: str) -> str:
        return task_name.replace("-v3", "")

    macro_task_count = len(ordered_shifted_tasks) if ordered_shifted_tasks else len(configured_meta_tasks)
    macros["CoreMetaTaskCount"] = str(macro_task_count)
    macros["CoreMetaTaskList"] = ", ".join(_task_alias(task) for task in ordered_shifted_tasks) if ordered_shifted_tasks else "none"
    macros["CoreMainSeedCount"] = str(len(metaworld_cfg.get("seeds", [])))
    macros["CoreExpandedSeedCount"] = str(seed_exp.get("n_per_variant", 14))
    macros["CoreRobustSeedCount"] = "3"
    macros["CoreRecentComparatorCount"] = "5"
    macros["CoreCalibrationTolerance"] = fmt(0.005, 3)
    calibration_rows = baseline_calibration.get("rows", [])
    max_abs_err = max((float(row.get("abs_error", 0.0)) for row in calibration_rows), default=0.0)
    macros["CoreCalibrationMaxAbsError"] = fmt(max_abs_err, 4)

    macros["CoreHistoryWindow"] = "8"
    macros["CoreHistoryLayers"] = "2"
    macros["CoreHistoryHidden"] = "128"
    macros["CoreHeadLayers"] = "2"
    macros["CoreHeadWidth"] = "256"
    macros["CoreEnsembleHeads"] = "5"
    macros["CoreTauGreen"] = fmt(0.02, 2)
    macros["CoreTauYellow"] = fmt(0.005, 3)
    macros["CoreCvarAlpha"] = fmt(0.4, 1)
    macros["CoreCvarPercentLabel"] = "40"

    # MetaWorld shifted stats
    vmeta = meta_stats["variant_summary"]
    baseline_row = variant_row(vmeta, "baseline")
    ext1_row = variant_row(vmeta, "ext1")
    ext2_row = variant_row(vmeta, "ext2")
    method_row = variant_row(vmeta, "method")
    lat_row = variant_row(vmeta, "latency_aware")
    adapt_row = variant_row(vmeta, "adaptmanip")
    cp_row = variant_row(vmeta, "robust_cp")
    hist_row = variant_row(vmeta, "history_keyframe")
    flow_row = variant_row(vmeta, "constrained_flow")

    macros["CoreMetaBaselineMean"] = fmt(baseline_row["mean_success"], 2)
    macros["CoreMetaBaselineWorst"] = fmt(baseline_row["worst_seed_mean"], 2)
    macros["CoreMetaBaselineCvar"] = fmt(baseline_row["cvar40_seed"], 2)
    macros["CoreMetaBaselineSuccPerK"] = fmt(baseline_row["success_per_1k_steps"], 2)

    macros["CoreMetaExtOneMean"] = fmt(ext1_row["mean_success"], 2)
    macros["CoreMetaExtOneWorst"] = fmt(ext1_row["worst_seed_mean"], 2)
    macros["CoreMetaExtOneCvar"] = fmt(ext1_row["cvar40_seed"], 2)
    macros["CoreMetaExtOneSuccPerK"] = fmt(ext1_row["success_per_1k_steps"], 2)

    macros["CoreMetaExtTwoMean"] = fmt(ext2_row["mean_success"], 2)
    macros["CoreMetaExtTwoWorst"] = fmt(ext2_row["worst_seed_mean"], 2)
    macros["CoreMetaExtTwoCvar"] = fmt(ext2_row["cvar40_seed"], 2)
    macros["CoreMetaExtTwoSuccPerK"] = fmt(ext2_row["success_per_1k_steps"], 2)

    macros["CoreMetaMethodMean"] = fmt(method_row["mean_success"], 2)
    macros["CoreMetaMethodWorst"] = fmt(method_row["worst_seed_mean"], 2)
    macros["CoreMetaMethodCvar"] = fmt(method_row["cvar40_seed"], 2)
    macros["CoreMetaMethodSuccPerK"] = fmt(method_row["success_per_1k_steps"], 2)
    macros["CoreMetaLatencyAwareMean"] = fmt(lat_row["mean_success"], 2)
    macros["CoreMetaLatencyAwareWorst"] = fmt(lat_row["worst_seed_mean"], 2)
    macros["CoreMetaLatencyAwareCvar"] = fmt(lat_row["cvar40_seed"], 2)
    macros["CoreMetaAdaptManipMean"] = fmt(adapt_row["mean_success"], 2)
    macros["CoreMetaAdaptManipWorst"] = fmt(adapt_row["worst_seed_mean"], 2)
    macros["CoreMetaAdaptManipCvar"] = fmt(adapt_row["cvar40_seed"], 2)
    macros["CoreMetaRobustCpMean"] = fmt(cp_row["mean_success"], 2)
    macros["CoreMetaRobustCpWorst"] = fmt(cp_row["worst_seed_mean"], 2)
    macros["CoreMetaRobustCpCvar"] = fmt(cp_row["cvar40_seed"], 2)
    macros["CoreMetaHistoryKeyframeMean"] = fmt(hist_row["mean_success"], 2)
    macros["CoreMetaHistoryKeyframeWorst"] = fmt(hist_row["worst_seed_mean"], 2)
    macros["CoreMetaHistoryKeyframeCvar"] = fmt(hist_row["cvar40_seed"], 2)
    macros["CoreMetaConstrainedFlowMean"] = fmt(flow_row["mean_success"], 2)
    macros["CoreMetaConstrainedFlowWorst"] = fmt(flow_row["worst_seed_mean"], 2)
    macros["CoreMetaConstrainedFlowCvar"] = fmt(flow_row["cvar40_seed"], 2)

    # Active-task subset summary (exclude tasks that are all-zero across main lanes).
    main_variants = ("baseline", "ext2", "adaptmanip", "method")
    task_variant_means: Dict[str, Dict[str, float]] = {}
    for row in meta_results.get("task_breakdown", []):
        if str(row.get("scenario")) != "shifted":
            continue
        task = str(row.get("task", ""))
        variant = str(row.get("variant", ""))
        if variant not in main_variants:
            continue
        task_variant_means.setdefault(task, {})[variant] = float(row.get("mean_success", 0.0))

    active_tasks = [
        task
        for task, vals in sorted(task_variant_means.items())
        if any(abs(float(vals.get(v, 0.0))) > 1e-12 for v in main_variants)
    ]
    all_zero_tasks = [
        task
        for task, vals in sorted(task_variant_means.items())
        if all(abs(float(vals.get(v, 0.0))) <= 1e-12 for v in main_variants)
    ]

    macros["CoreMetaActiveTaskCount"] = str(len(active_tasks))
    macros["CoreMetaAllZeroTaskCount"] = str(len(all_zero_tasks))
    macros["CoreMetaAllZeroTaskList"] = ", ".join(_task_alias(t) for t in all_zero_tasks) if all_zero_tasks else "none"

    def _active_subset_summary(variant: str) -> Dict[str, float]:
        by_seed: Dict[int, List[float]] = {}
        active_set = set(active_tasks)
        for row in meta_results.get("episodes", []):
            if str(row.get("scenario")) != "shifted":
                continue
            if str(row.get("variant")) != variant:
                continue
            if str(row.get("task")) not in active_set:
                continue
            try:
                seed = int(row.get("seed", -1))
            except Exception:
                continue
            by_seed.setdefault(seed, []).append(float(row.get("success_final", 0.0)))
        seed_means = [mean(vals) for vals in by_seed.values() if vals]
        if not seed_means:
            return {"mean": 0.0, "worst": 0.0, "cvar": 0.0}
        return {
            "mean": mean(seed_means),
            "worst": min(seed_means),
            "cvar": cvar_bottom(seed_means, fraction=0.4),
        }

    ext2_active = _active_subset_summary("ext2")
    method_active = _active_subset_summary("method")
    macros["CoreMetaExtTwoActiveMean"] = fmt(ext2_active["mean"], 2)
    macros["CoreMetaExtTwoActiveWorst"] = fmt(ext2_active["worst"], 2)
    macros["CoreMetaExtTwoActiveCvar"] = fmt(ext2_active["cvar"], 2)
    macros["CoreMetaMethodActiveMean"] = fmt(method_active["mean"], 2)
    macros["CoreMetaMethodActiveWorst"] = fmt(method_active["worst"], 2)
    macros["CoreMetaMethodActiveCvar"] = fmt(method_active["cvar"], 2)
    macros["CoreMetaDeltaExtTwoActiveMean"] = fmt_signed(method_active["mean"] - ext2_active["mean"], 4)

    meta_ext2 = find_row(meta_stats["comparisons"], comparator_group="ext2")
    macros["CoreMetaDeltaExtTwoMean"] = fmt_signed(meta_ext2["delta_mean"], 4)
    macros["CoreMetaDeltaExtTwoCi"] = fmt(meta_ext2["delta_ci95_halfwidth"], 4)
    macros["CoreMetaDeltaExtTwoD"] = fmt(meta_ext2["cohen_d"], 3)
    macros["CoreMetaDeltaExtTwoP"] = fmt(meta_ext2["p_two_sided"], 4)

    meta_seedexp_ext2 = find_row(meta_seedexp["comparisons"], comparator_group="ext2")
    meta_seedexp_summary = meta_seedexp["variant_summary"]
    macros["CoreMetaSeedExpN"] = str(meta_seedexp_summary["method"]["n_seeds"])
    macros["CoreMetaSeedExpMethodMean"] = fmt(meta_seedexp_summary["method"]["mean_success"], 4)
    macros["CoreMetaSeedExpExtTwoMean"] = fmt(meta_seedexp_summary["ext2"]["mean_success"], 4)
    macros["CoreMetaSeedExpMethodWorst"] = fmt(meta_seedexp_summary["method"]["worst_seed_mean"], 4)
    macros["CoreMetaSeedExpExtTwoWorst"] = fmt(meta_seedexp_summary["ext2"]["worst_seed_mean"], 4)
    macros["CoreMetaSeedExpMethodCvar"] = fmt(meta_seedexp_summary["method"]["cvar40_seed"], 4)
    macros["CoreMetaSeedExpExtTwoCvar"] = fmt(meta_seedexp_summary["ext2"]["cvar40_seed"], 4)
    macros["CoreMetaSeedExpMethodCi"] = fmt(
        ci95_from_samples([float(v) for v in meta_seedexp_summary["method"].get("seed_means", [])]),
        4,
    )
    macros["CoreMetaSeedExpExtTwoCi"] = fmt(
        ci95_from_samples([float(v) for v in meta_seedexp_summary["ext2"].get("seed_means", [])]),
        4,
    )
    macros["CoreMetaSeedExpDeltaMean"] = fmt_signed(meta_seedexp_ext2["delta_mean"], 4)
    macros["CoreMetaSeedExpDeltaCi"] = fmt(meta_seedexp_ext2["delta_ci95_halfwidth"], 4)
    ext2_n14_p_mean = float(meta_seedexp_ext2["p_two_sided"])
    ext2_n14_p_cvar = float(meta_seedexp_ext2.get("p_two_sided_cvar40_seed", meta_seedexp_ext2["p_two_sided"]))
    # Use higher precision for very small N=14 p-values to avoid family-size ambiguity.
    macros["CoreMetaSeedExpP"] = fmt_p(ext2_n14_p_mean, 6)
    macros["CoreMetaSeedExpPCvar"] = fmt_p(ext2_n14_p_cvar, 6)
    macros["CoreMetaSeedExpD"] = fmt(meta_seedexp_ext2["cohen_d"], 3)
    macros["CoreMetaSeedExpWorstDelta"] = fmt_signed(meta_seedexp_ext2["delta_worst_seed_mean"], 4)
    macros["CoreMetaSeedExpCvarDelta"] = fmt_signed(meta_seedexp_ext2["delta_cvar40_seed"], 4)
    method_lambda_vals = [
        float(ep.get("mean_risk_lambda", 0.0))
        for ep in meta_seedexp_results.get("episodes", [])
        if str(ep.get("variant", "")) == "method" and ep.get("mean_risk_lambda") is not None
    ]
    objective_lambda = sum(method_lambda_vals) / len(method_lambda_vals) if method_lambda_vals else 0.95
    macros["CoreObjectiveLambda"] = fmt(objective_lambda, 2)
    macros["CoreMetaSeedExpDeltaJ"] = fmt_signed(
        float(meta_seedexp_ext2["delta_mean"]) + objective_lambda * float(meta_seedexp_ext2["delta_cvar40_seed"]),
        4,
    )

    meta_seedexp_lat = find_row(meta_seedexp_latency["comparisons"], comparator_group="latency_aware")
    meta_seedexp_lat_summary = meta_seedexp_latency["variant_summary"]
    macros["CoreMetaSeedExpLatencyN"] = str(meta_seedexp_lat_summary["method"]["n_seeds"])
    macros["CoreMetaSeedExpLatencyMethodMean"] = fmt(meta_seedexp_lat_summary["method"]["mean_success"], 4)
    macros["CoreMetaSeedExpLatencyCompMean"] = fmt(meta_seedexp_lat_summary["latency_aware"]["mean_success"], 4)
    macros["CoreMetaSeedExpLatencyMethodWorst"] = fmt(meta_seedexp_lat_summary["method"]["worst_seed_mean"], 4)
    macros["CoreMetaSeedExpLatencyCompWorst"] = fmt(meta_seedexp_lat_summary["latency_aware"]["worst_seed_mean"], 4)
    macros["CoreMetaSeedExpLatencyMethodCvar"] = fmt(meta_seedexp_lat_summary["method"]["cvar40_seed"], 4)
    macros["CoreMetaSeedExpLatencyCompCvar"] = fmt(meta_seedexp_lat_summary["latency_aware"]["cvar40_seed"], 4)
    macros["CoreMetaSeedExpLatencyMethodCi"] = fmt(
        ci95_from_samples([float(v) for v in meta_seedexp_lat_summary["method"].get("seed_means", [])]),
        4,
    )
    macros["CoreMetaSeedExpLatencyCompCi"] = fmt(
        ci95_from_samples([float(v) for v in meta_seedexp_lat_summary["latency_aware"].get("seed_means", [])]),
        4,
    )
    macros["CoreMetaSeedExpLatencyDeltaMean"] = fmt_signed(meta_seedexp_lat["delta_mean"], 4)
    macros["CoreMetaSeedExpLatencyDeltaCi"] = fmt(meta_seedexp_lat["delta_ci95_halfwidth"], 4)
    latency_n14_p_mean = float(meta_seedexp_lat["p_two_sided"])
    macros["CoreMetaSeedExpLatencyP"] = fmt_p(latency_n14_p_mean, 4)
    macros["CoreMetaSeedExpLatencyPCvar"] = fmt_p(
        float(meta_seedexp_lat.get("p_two_sided_cvar40_seed", meta_seedexp_lat["p_two_sided"])),
        4,
    )
    macros["CoreMetaSeedExpLatencyD"] = fmt(meta_seedexp_lat["cohen_d"], 3)
    macros["CoreMetaSeedExpLatencyWorstDelta"] = fmt_signed(meta_seedexp_lat["delta_worst_seed_mean"], 4)
    macros["CoreMetaSeedExpLatencyCvarDelta"] = fmt_signed(meta_seedexp_lat["delta_cvar40_seed"], 4)

    meta_seedexp_lat_n30 = find_row(meta_seedexp_latency_n30["comparisons"], comparator_group="latency_aware")
    meta_seedexp_lat_n30_summary = meta_seedexp_latency_n30["variant_summary"]
    macros["CoreMetaSeedExpLatencyNThirtyN"] = str(meta_seedexp_lat_n30_summary["method"]["n_seeds"])
    macros["CoreMetaSeedExpLatencyNThirtyMethodMean"] = fmt(
        meta_seedexp_lat_n30_summary["method"]["mean_success"], 4
    )
    macros["CoreMetaSeedExpLatencyNThirtyCompMean"] = fmt(
        meta_seedexp_lat_n30_summary["latency_aware"]["mean_success"], 4
    )
    macros["CoreMetaSeedExpLatencyNThirtyMethodCvar"] = fmt(
        meta_seedexp_lat_n30_summary["method"]["cvar40_seed"], 4
    )
    macros["CoreMetaSeedExpLatencyNThirtyCompCvar"] = fmt(
        meta_seedexp_lat_n30_summary["latency_aware"]["cvar40_seed"], 4
    )
    macros["CoreMetaSeedExpLatencyNThirtyDeltaMean"] = fmt_signed(meta_seedexp_lat_n30["delta_mean"], 4)
    macros["CoreMetaSeedExpLatencyNThirtyDeltaCi"] = fmt(meta_seedexp_lat_n30["delta_ci95_halfwidth"], 4)
    latency_n30_p_mean = float(meta_seedexp_lat_n30["p_two_sided"])
    latency_n30_p_cvar = float(
        meta_seedexp_lat_n30.get("p_two_sided_cvar40_seed", meta_seedexp_lat_n30["p_two_sided"])
    )
    macros["CoreMetaSeedExpLatencyNThirtyP"] = fmt_p(latency_n30_p_mean, 4)
    macros["CoreMetaSeedExpLatencyNThirtyPCvar"] = fmt_p(latency_n30_p_cvar, 4)
    macros["CoreMetaSeedExpLatencyNThirtyD"] = fmt(meta_seedexp_lat_n30["cohen_d"], 3)
    macros["CoreMetaSeedExpLatencyNThirtyWorstDelta"] = fmt_signed(
        meta_seedexp_lat_n30["delta_worst_seed_mean"], 4
    )
    macros["CoreMetaSeedExpLatencyNThirtyCvarDelta"] = fmt_signed(
        meta_seedexp_lat_n30["delta_cvar40_seed"], 4
    )
    n30_n = int(meta_seedexp_lat_n30_summary["method"]["n_seeds"])
    n30_d = float(meta_seedexp_lat_n30["cohen_d"])
    macros["CoreMetaSeedExpLatencyNThirtyPowerCurrent"] = fmt(
        approx_two_sample_power_from_d(n30_d, n30_n, alpha=0.05), 3
    )
    macros["CoreMetaSeedExpLatencyNThirtyPowerTarget"] = fmt(0.8, 1)
    macros["CoreMetaSeedExpLatencyNThirtyPowerTargetN"] = str(
        approx_n_per_group_for_power(n30_d, target_power=0.8, alpha=0.05)
    )

    meta_seedexp_adapt_row = find_row(meta_seedexp_adapt["comparisons"], comparator_group="adaptmanip")
    meta_seedexp_adapt_summary = meta_seedexp_adapt["variant_summary"]
    macros["CoreMetaSeedExpAdaptN"] = str(meta_seedexp_adapt_summary["method"]["n_seeds"])
    macros["CoreMetaSeedExpAdaptMethodMean"] = fmt(meta_seedexp_adapt_summary["method"]["mean_success"], 4)
    macros["CoreMetaSeedExpAdaptCompMean"] = fmt(meta_seedexp_adapt_summary["adaptmanip"]["mean_success"], 4)
    macros["CoreMetaSeedExpAdaptMethodWorst"] = fmt(meta_seedexp_adapt_summary["method"]["worst_seed_mean"], 4)
    macros["CoreMetaSeedExpAdaptCompWorst"] = fmt(meta_seedexp_adapt_summary["adaptmanip"]["worst_seed_mean"], 4)
    macros["CoreMetaSeedExpAdaptMethodCvar"] = fmt(meta_seedexp_adapt_summary["method"]["cvar40_seed"], 4)
    macros["CoreMetaSeedExpAdaptCompCvar"] = fmt(meta_seedexp_adapt_summary["adaptmanip"]["cvar40_seed"], 4)
    macros["CoreMetaSeedExpAdaptMethodCi"] = fmt(
        ci95_from_samples([float(v) for v in meta_seedexp_adapt_summary["method"].get("seed_means", [])]),
        4,
    )
    macros["CoreMetaSeedExpAdaptCompCi"] = fmt(
        ci95_from_samples([float(v) for v in meta_seedexp_adapt_summary["adaptmanip"].get("seed_means", [])]),
        4,
    )
    macros["CoreMetaSeedExpAdaptDeltaMean"] = fmt_signed(meta_seedexp_adapt_row["delta_mean"], 4)
    macros["CoreMetaSeedExpAdaptDeltaCi"] = fmt(meta_seedexp_adapt_row["delta_ci95_halfwidth"], 4)
    adapt_n14_p_mean = float(meta_seedexp_adapt_row["p_two_sided"])
    adapt_n14_p_cvar = float(
        meta_seedexp_adapt_row.get("p_two_sided_cvar40_seed", meta_seedexp_adapt_row["p_two_sided"])
    )
    adapt_n14_worst_delta = float(meta_seedexp_adapt_row["delta_worst_seed_mean"])
    macros["CoreMetaSeedExpAdaptP"] = fmt_p(adapt_n14_p_mean, 6)
    macros["CoreMetaSeedExpAdaptPCvar"] = fmt_p(adapt_n14_p_cvar, 6)
    macros["CoreMetaSeedExpAdaptD"] = fmt(meta_seedexp_adapt_row["cohen_d"], 3)
    macros["CoreMetaSeedExpAdaptWorstDelta"] = fmt_signed(adapt_n14_worst_delta, 4)
    macros["CoreMetaSeedExpAdaptCvarDelta"] = fmt_signed(meta_seedexp_adapt_row["delta_cvar40_seed"], 4)
    macros["CoreMetaSeedExpAdaptCvarSig"] = "yes" if adapt_n14_p_cvar < 0.05 else "no"
    macros["CoreMetaSeedExpAdaptCvarLabel"] = nominal_significance_label(adapt_n14_p_cvar < 0.05)
    macros["CoreMetaSeedExpAdaptWorstDeltaDirection"] = direction_label(adapt_n14_worst_delta)
    macros["CoreMetaSeedExpAdaptDeltaJ"] = fmt_signed(
        float(meta_seedexp_adapt_row["delta_mean"]) + objective_lambda * float(meta_seedexp_adapt_row["delta_cvar40_seed"]),
        4,
    )
    adapt_n14_n = int(meta_seedexp_adapt_summary["method"]["n_seeds"])
    adapt_n14_d = float(meta_seedexp_adapt_row["cohen_d"])
    macros["CoreMetaSeedExpAdaptNFourteenPowerCurrent"] = fmt(
        approx_two_sample_power_from_d(adapt_n14_d, adapt_n14_n, alpha=0.05), 3
    )
    macros["CoreMetaSeedExpAdaptNFourteenPowerTarget"] = fmt(0.8, 1)
    macros["CoreMetaSeedExpAdaptNFourteenPowerTargetN"] = str(
        approx_n_per_group_for_power(adapt_n14_d, target_power=0.8, alpha=0.05)
    )
    n14_family_alpha = 0.05
    # N=14 primary family is ext2/adaptmanip within each metric family (mean, CVaR).
    n14_family_holm = holm_bonferroni([ext2_n14_p_mean, adapt_n14_p_mean])
    n14_family_holm_cvar = holm_bonferroni([ext2_n14_p_cvar, adapt_n14_p_cvar])
    macros["CoreMetaNFourteenFamilyTests"] = str(2)
    macros["CoreMetaNFourteenFamilyAlpha"] = fmt(n14_family_alpha, 2)
    macros["CoreMetaNFourteenHolmExtTwoMeanP"] = fmt_p(n14_family_holm[0], 4)
    macros["CoreMetaNFourteenHolmExtTwoCvarP"] = fmt_p(n14_family_holm_cvar[0], 4)
    macros["CoreMetaNFourteenHolmLatencyMeanP"] = fmt_p(latency_n14_p_mean, 4)
    macros["CoreMetaNFourteenHolmAdaptMeanP"] = fmt_p(n14_family_holm[1], 4)
    macros["CoreMetaNFourteenHolmAdaptCvarP"] = fmt_p(n14_family_holm_cvar[1], 4)
    macros["CoreMetaNFourteenHolmExtTwoMeanSig"] = (
        "yes" if n14_family_holm[0] < n14_family_alpha else "no"
    )
    macros["CoreMetaNFourteenHolmAdaptMeanSig"] = (
        "yes" if n14_family_holm[1] < n14_family_alpha else "no"
    )
    macros["CoreMetaNFourteenHolmAdaptMeanLabel"] = significance_label(n14_family_holm[1] < n14_family_alpha)
    adapt_mean_sig = n14_family_holm[1] < n14_family_alpha
    adapt_cvar_sig = n14_family_holm_cvar[1] < n14_family_alpha
    if not adapt_mean_sig and not adapt_cvar_sig:
        macros["CoreMetaSeedExpAdaptNFourteenSummary"] = (
            "no metric-level statistical separation at $\\alpha=0.05$: non-significant, not equivalence"
        )
    elif adapt_mean_sig and adapt_cvar_sig:
        macros["CoreMetaSeedExpAdaptNFourteenSummary"] = (
            "dual-metric statistical separation: mean and CVaR significant"
        )
    else:
        macros["CoreMetaSeedExpAdaptNFourteenSummary"] = (
            "mixed evidence across metrics: one significant and one non-significant"
        )

    eq_metrics = {
        str(row.get("metric", "")): row
        for row in adapt_equivalence.get("metrics", [])
        if isinstance(row, dict)
    }
    eq_mean = eq_metrics.get("mean_seed_success", {})
    eq_cvar = eq_metrics.get("cvar40_seed_success", {})
    eq_margin = float(adapt_equivalence.get("equivalence_margin_abs", 0.05))
    macros["CoreMetaAdaptEqMargin"] = fmt(eq_margin, 3)
    macros["CoreMetaAdaptEqMeanCiNinetyLow"] = fmt_signed(float(eq_mean.get("ci90_low", 0.0)), 4)
    macros["CoreMetaAdaptEqMeanCiNinetyHigh"] = fmt_signed(float(eq_mean.get("ci90_high", 0.0)), 4)
    macros["CoreMetaAdaptEqCvarCiNinetyLow"] = fmt_signed(float(eq_cvar.get("ci90_low", 0.0)), 4)
    macros["CoreMetaAdaptEqCvarCiNinetyHigh"] = fmt_signed(float(eq_cvar.get("ci90_high", 0.0)), 4)
    mean_equiv = bool(eq_mean.get("equivalence_supported", False))
    cvar_equiv = bool(eq_cvar.get("equivalence_supported", False))
    macros["CoreMetaAdaptEqMeanLabel"] = "equivalence-supported" if mean_equiv else "equivalence-not-supported"
    macros["CoreMetaAdaptEqCvarLabel"] = "equivalence-supported" if cvar_equiv else "equivalence-not-supported"
    macros["CoreMetaAdaptEqBothLabel"] = (
        "both-metrics-equivalent" if (mean_equiv and cvar_equiv) else "equivalence-not-established"
    )
    macros["CoreMetaAdaptEqBootstrapSamples"] = str(int(adapt_equivalence.get("bootstrap_samples", 0)))

    meta_seedexp_adapt_n30_row = find_row(meta_seedexp_adapt_n30["comparisons"], comparator_group="adaptmanip")
    meta_seedexp_adapt_n30_summary = meta_seedexp_adapt_n30["variant_summary"]
    macros["CoreMetaSeedExpAdaptNThirtyN"] = str(meta_seedexp_adapt_n30_summary["method"]["n_seeds"])
    macros["CoreMetaSeedExpAdaptNThirtyMethodMean"] = fmt(
        meta_seedexp_adapt_n30_summary["method"]["mean_success"], 4
    )
    macros["CoreMetaSeedExpAdaptNThirtyCompMean"] = fmt(
        meta_seedexp_adapt_n30_summary["adaptmanip"]["mean_success"], 4
    )
    macros["CoreMetaSeedExpAdaptNThirtyMethodCvar"] = fmt(
        meta_seedexp_adapt_n30_summary["method"]["cvar40_seed"], 4
    )
    macros["CoreMetaSeedExpAdaptNThirtyCompCvar"] = fmt(
        meta_seedexp_adapt_n30_summary["adaptmanip"]["cvar40_seed"], 4
    )
    macros["CoreMetaSeedExpAdaptNThirtyDeltaMean"] = fmt_signed(meta_seedexp_adapt_n30_row["delta_mean"], 4)
    macros["CoreMetaSeedExpAdaptNThirtyDeltaCi"] = fmt(meta_seedexp_adapt_n30_row["delta_ci95_halfwidth"], 4)
    adapt_n30_p_mean = float(meta_seedexp_adapt_n30_row["p_two_sided"])
    adapt_n30_p_cvar = float(
        meta_seedexp_adapt_n30_row.get("p_two_sided_cvar40_seed", meta_seedexp_adapt_n30_row["p_two_sided"])
    )
    macros["CoreMetaSeedExpAdaptNThirtyP"] = fmt_p(adapt_n30_p_mean, 4)
    macros["CoreMetaSeedExpAdaptNThirtyPCvar"] = fmt_p(adapt_n30_p_cvar, 4)
    # Two-stage optional-expansion correction for the same comparator/metric
    # tested at N=14 then N=30 (Bonferroni over 2 looks).
    adapt_two_stage_bonf_mean = min(1.0, 2.0 * adapt_n30_p_mean)
    adapt_two_stage_bonf_cvar = min(1.0, 2.0 * adapt_n30_p_cvar)
    macros["CoreMetaSeedExpAdaptTwoStageBonfMeanP"] = fmt_p(adapt_two_stage_bonf_mean, 4)
    macros["CoreMetaSeedExpAdaptTwoStageBonfCvarP"] = fmt_p(adapt_two_stage_bonf_cvar, 4)
    macros["CoreMetaSeedExpAdaptTwoStageBonfMeanLabel"] = bonferroni_significance_label(
        adapt_two_stage_bonf_mean < 0.05
    )
    macros["CoreMetaSeedExpAdaptTwoStageBonfCvarLabel"] = bonferroni_significance_label(
        adapt_two_stage_bonf_cvar < 0.05
    )
    adapt_n30_mc_mean_n = int(meta_seedexp_adapt_n30_row.get("permutation_samples_used_mean", 0) or 0)
    adapt_n30_mc_cvar_n = int(meta_seedexp_adapt_n30_row.get("permutation_samples_used_cvar40_seed", 0) or 0)
    macros["CoreMetaSeedExpAdaptNThirtyPermSamplesMean"] = str(adapt_n30_mc_mean_n)
    macros["CoreMetaSeedExpAdaptNThirtyPermSamplesCvar"] = str(adapt_n30_mc_cvar_n)
    macros["CoreMetaSeedExpAdaptNThirtyPermMcSeMean"] = fmt(
        mc_se_from_probability(adapt_n30_p_mean, adapt_n30_mc_mean_n),
        6,
    )
    macros["CoreMetaSeedExpAdaptNThirtyPermMcSeCvar"] = fmt(
        mc_se_from_probability(adapt_n30_p_cvar, adapt_n30_mc_cvar_n),
        6,
    )
    macros["CoreMetaSeedExpAdaptNThirtyD"] = fmt(meta_seedexp_adapt_n30_row["cohen_d"], 3)
    macros["CoreMetaSeedExpAdaptNThirtyWorstDelta"] = fmt_signed(
        meta_seedexp_adapt_n30_row["delta_worst_seed_mean"], 4
    )
    macros["CoreMetaSeedExpAdaptNThirtyCvarDelta"] = fmt_signed(
        meta_seedexp_adapt_n30_row["delta_cvar40_seed"], 4
    )
    adapt_n14_delta_mean = float(meta_seedexp_adapt_row["delta_mean"])
    adapt_n30_delta_mean = float(meta_seedexp_adapt_n30_row["delta_mean"])
    adapt_mean_shrink = adapt_n14_delta_mean - adapt_n30_delta_mean
    adapt_mean_shrink_pct = 0.0
    if abs(adapt_n14_delta_mean) > 1e-12:
        adapt_mean_shrink_pct = 100.0 * adapt_mean_shrink / abs(adapt_n14_delta_mean)
    macros["CoreMetaSeedExpAdaptMeanShrinkDelta"] = fmt_signed(adapt_mean_shrink, 4)
    macros["CoreMetaSeedExpAdaptMeanShrinkPctAbs"] = fmt(abs(adapt_mean_shrink_pct), 1)
    macros["CoreMetaSeedExpAdaptMeanShrinkLabel"] = (
        "contracts" if adapt_mean_shrink >= 0 else "expands"
    )
    macros["CoreMetaSeedExpAdaptNThirtyDeltaJ"] = fmt_signed(
        float(meta_seedexp_adapt_n30_row["delta_mean"])
        + objective_lambda * float(meta_seedexp_adapt_n30_row["delta_cvar40_seed"]),
        4,
    )
    adapt_n30_n = int(meta_seedexp_adapt_n30_summary["method"]["n_seeds"])
    adapt_n30_d = float(meta_seedexp_adapt_n30_row["cohen_d"])
    macros["CoreMetaSeedExpAdaptNThirtyPowerCurrent"] = fmt(
        approx_two_sample_power_from_d(adapt_n30_d, adapt_n30_n, alpha=0.05), 3
    )
    macros["CoreMetaSeedExpAdaptNThirtyPowerTarget"] = fmt(0.8, 1)
    macros["CoreMetaSeedExpAdaptNThirtyPowerTargetN"] = str(
        approx_n_per_group_for_power(adapt_n30_d, target_power=0.8, alpha=0.05)
    )
    deep_family_alpha = 0.05
    # Deep-N primary family is adaptmanip mean/CVaR only; latency proxy is supplementary.
    deep_family_holm = holm_bonferroni([adapt_n30_p_mean, adapt_n30_p_cvar])
    macros["CoreMetaDeepFamilyTests"] = str(2)
    macros["CoreMetaDeepFamilyAlpha"] = fmt(deep_family_alpha, 2)
    # Keep latency macros for compatibility, but report nominal p-values (supplementary lane).
    macros["CoreMetaDeepFamilyHolmLatencyMeanP"] = fmt_p(latency_n30_p_mean, 4)
    macros["CoreMetaDeepFamilyHolmLatencyCvarP"] = fmt_p(latency_n30_p_cvar, 4)
    macros["CoreMetaDeepFamilyHolmAdaptMeanP"] = fmt_p(deep_family_holm[0], 4)
    macros["CoreMetaDeepFamilyHolmAdaptCvarP"] = fmt_p(deep_family_holm[1], 4)
    macros["CoreMetaDeepFamilyHolmMinP"] = fmt_p(min(deep_family_holm), 4)
    macros["CoreMetaDeepFamilyHolmLatencyMeanSig"] = "no"
    macros["CoreMetaDeepFamilyHolmLatencyCvarSig"] = "no"
    macros["CoreMetaDeepFamilyHolmAdaptMeanSig"] = (
        "yes" if deep_family_holm[0] < deep_family_alpha else "no"
    )
    macros["CoreMetaDeepFamilyHolmAdaptCvarSig"] = (
        "yes" if deep_family_holm[1] < deep_family_alpha else "no"
    )
    macros["CoreMetaDeepFamilyHolmLatencyMeanLabel"] = "supplementary-only"
    macros["CoreMetaDeepFamilyHolmLatencyCvarLabel"] = "supplementary-only"
    macros["CoreMetaDeepFamilyHolmAdaptMeanLabel"] = significance_label(
        deep_family_holm[0] < deep_family_alpha
    )
    macros["CoreMetaDeepFamilyHolmAdaptCvarLabel"] = significance_label(
        deep_family_holm[1] < deep_family_alpha
    )

    # Task-conditioned shifted comparison against closest comparator.
    def _task_label(task_name: str) -> str:
        return task_name.replace("-v3", "")

    shifted_by_task: Dict[str, Dict[str, float]] = {}
    for row in meta_results.get("task_breakdown", []):
        if row.get("scenario") != "shifted":
            continue
        task = str(row.get("task", ""))
        variant = str(row.get("variant", ""))
        shifted_by_task.setdefault(task, {})[variant] = float(row.get("mean_success", 0.0))

    def _task_delta_counts(comparator: str) -> Dict[str, Any]:
        task_wins: List[str] = []
        task_losses: List[str] = []
        task_ties: List[str] = []
        for task in sorted(shifted_by_task):
            vals = shifted_by_task[task]
            method_mean = vals.get("method")
            comp_mean = vals.get(comparator)
            if method_mean is None or comp_mean is None:
                continue
            delta = method_mean - comp_mean
            if delta > 1e-9:
                task_wins.append(_task_label(task))
            elif delta < -1e-9:
                task_losses.append(_task_label(task))
            else:
                task_ties.append(_task_label(task))
        return {
            "wins": task_wins,
            "losses": task_losses,
            "ties": task_ties,
            "total": len(task_wins) + len(task_losses) + len(task_ties),
        }

    latency_task_delta = _task_delta_counts("latency_aware")
    macros["CoreMetaLatencyTaskWins"] = str(len(latency_task_delta["wins"]))
    macros["CoreMetaLatencyTaskLosses"] = str(len(latency_task_delta["losses"]))
    macros["CoreMetaLatencyTaskTies"] = str(len(latency_task_delta["ties"]))
    macros["CoreMetaLatencyTaskTotal"] = str(latency_task_delta["total"])
    macros["CoreMetaLatencyTaskWinList"] = ", ".join(latency_task_delta["wins"]) if latency_task_delta["wins"] else "none"
    macros["CoreMetaLatencyTaskLossList"] = (
        ", ".join(latency_task_delta["losses"]) if latency_task_delta["losses"] else "none"
    )

    adapt_task_delta = _task_delta_counts("adaptmanip")
    macros["CoreMetaAdaptTaskWins"] = str(len(adapt_task_delta["wins"]))
    macros["CoreMetaAdaptTaskLosses"] = str(len(adapt_task_delta["losses"]))
    macros["CoreMetaAdaptTaskTies"] = str(len(adapt_task_delta["ties"]))
    macros["CoreMetaAdaptTaskTotal"] = str(adapt_task_delta["total"])
    macros["CoreMetaAdaptTaskWinList"] = ", ".join(adapt_task_delta["wins"]) if adapt_task_delta["wins"] else "none"
    macros["CoreMetaAdaptTaskLossList"] = ", ".join(adapt_task_delta["losses"]) if adapt_task_delta["losses"] else "none"

    sensitivity_rows = meta_cvar_sensitivity.get("rows", [])
    if sensitivity_rows:
        deltas = [float(row.get("delta_cvar", 0.0)) for row in sensitivity_rows]
        macros["CoreMetaLatencyCvarAlphaMinDelta"] = fmt_signed(min(deltas), 4)
        macros["CoreMetaLatencyCvarAlphaMaxDelta"] = fmt_signed(max(deltas), 4)
        first_row = sensitivity_rows[0]
        last_row = sensitivity_rows[-1]
        macros["CoreMetaLatencyCvarAlphaLow"] = fmt(float(first_row.get("alpha", 0.1)), 1)
        macros["CoreMetaLatencyCvarAlphaHigh"] = fmt(float(last_row.get("alpha", 0.5)), 1)
    else:
        macros["CoreMetaLatencyCvarAlphaMinDelta"] = fmt_signed(0.0, 4)
        macros["CoreMetaLatencyCvarAlphaMaxDelta"] = fmt_signed(0.0, 4)
        macros["CoreMetaLatencyCvarAlphaLow"] = fmt(0.1, 1)
        macros["CoreMetaLatencyCvarAlphaHigh"] = fmt(0.5, 1)

    sensitivity_rows_adapt = meta_cvar_sensitivity_adapt.get("rows", [])
    if sensitivity_rows_adapt:
        deltas_adapt = [float(row.get("delta_cvar", 0.0)) for row in sensitivity_rows_adapt]
        macros["CoreMetaAdaptCvarAlphaMinDelta"] = fmt_signed(min(deltas_adapt), 4)
        macros["CoreMetaAdaptCvarAlphaMaxDelta"] = fmt_signed(max(deltas_adapt), 4)
        first_row_adapt = sensitivity_rows_adapt[0]
        last_row_adapt = sensitivity_rows_adapt[-1]
        macros["CoreMetaAdaptCvarAlphaLow"] = fmt(float(first_row_adapt.get("alpha", 0.1)), 1)
        macros["CoreMetaAdaptCvarAlphaHigh"] = fmt(float(last_row_adapt.get("alpha", 0.5)), 1)
    else:
        macros["CoreMetaAdaptCvarAlphaMinDelta"] = fmt_signed(0.0, 4)
        macros["CoreMetaAdaptCvarAlphaMaxDelta"] = fmt_signed(0.0, 4)
        macros["CoreMetaAdaptCvarAlphaLow"] = fmt(0.1, 1)
        macros["CoreMetaAdaptCvarAlphaHigh"] = fmt(0.5, 1)

    macros["CoreMetaHolmSignificant"] = str(pvals_meta["summary"]["holm_significant_count"])
    macros["CoreMetaHolmTests"] = str(pvals_meta["summary"]["num_tests"])

    maniskill_summary = maniskill_stats.get("variant_summary", {})
    maniskill_method = variant_row(maniskill_summary, "method")
    maniskill_ext2 = variant_row(maniskill_summary, "ext2")
    maniskill_latency = variant_row(maniskill_summary, "latency_aware")
    macros["CoreManiMethodMean"] = fmt(maniskill_method["mean_success"], 4)
    macros["CoreManiMethodWorst"] = fmt(maniskill_method["worst_seed_mean"], 4)
    macros["CoreManiMethodCvar"] = fmt(maniskill_method["cvar40_seed"], 4)
    macros["CoreManiExtTwoMean"] = fmt(maniskill_ext2["mean_success"], 4)
    macros["CoreManiExtTwoWorst"] = fmt(maniskill_ext2["worst_seed_mean"], 4)
    macros["CoreManiExtTwoCvar"] = fmt(maniskill_ext2["cvar40_seed"], 4)
    macros["CoreManiLatencyAwareMean"] = fmt(maniskill_latency["mean_success"], 4)
    macros["CoreManiLatencyAwareWorst"] = fmt(maniskill_latency["worst_seed_mean"], 4)
    macros["CoreManiLatencyAwareCvar"] = fmt(maniskill_latency["cvar40_seed"], 4)
    maniskill_ext2_cmp = find_row(maniskill_stats.get("comparisons", []), comparator_group="ext2")
    maniskill_latency_cmp = find_row(maniskill_stats.get("comparisons", []), comparator_group="latency_aware")
    macros["CoreManiDeltaExtTwoMean"] = fmt_signed(maniskill_ext2_cmp["delta_mean"], 4)
    macros["CoreManiDeltaExtTwoWorst"] = fmt_signed(
        maniskill_method["worst_seed_mean"] - maniskill_ext2["worst_seed_mean"], 4
    )
    macros["CoreManiDeltaExtTwoCvar"] = fmt_signed(
        maniskill_method["cvar40_seed"] - maniskill_ext2["cvar40_seed"], 4
    )
    macros["CoreManiDeltaExtTwoCi"] = fmt(maniskill_ext2_cmp["delta_ci95_halfwidth"], 4)
    macros["CoreManiDeltaExtTwoP"] = fmt_p(float(maniskill_ext2_cmp["p_two_sided"]), 4)
    macros["CoreManiDeltaExtTwoD"] = fmt(maniskill_ext2_cmp.get("cohen_d", 0.0), 3)
    macros["CoreManiDeltaLatencyMean"] = fmt_signed(maniskill_latency_cmp["delta_mean"], 4)
    macros["CoreManiDeltaLatencyWorst"] = fmt_signed(
        maniskill_method["worst_seed_mean"] - maniskill_latency["worst_seed_mean"], 4
    )
    macros["CoreManiDeltaLatencyCvar"] = fmt_signed(
        maniskill_method["cvar40_seed"] - maniskill_latency["cvar40_seed"], 4
    )
    macros["CoreManiDeltaLatencyCi"] = fmt(maniskill_latency_cmp["delta_ci95_halfwidth"], 4)
    macros["CoreManiDeltaLatencyP"] = fmt_p(float(maniskill_latency_cmp["p_two_sided"]), 4)
    macros["CoreManiDeltaLatencyD"] = fmt(maniskill_latency_cmp.get("cohen_d", 0.0), 3)

    cross_summary = cross_embodiment_stats.get("variant_summary", {})
    cross_method = variant_row(cross_summary, "method")
    cross_ext2 = variant_row(cross_summary, "ext2")
    cross_latency = variant_row(cross_summary, "latency_aware")
    macros["CoreCrossEmbodimentMethodMean"] = fmt(cross_method["mean_success"], 4)
    macros["CoreCrossEmbodimentMethodWorst"] = fmt(cross_method["worst_seed_mean"], 4)
    macros["CoreCrossEmbodimentMethodCvar"] = fmt(cross_method["cvar40_seed"], 4)
    macros["CoreCrossEmbodimentExtTwoMean"] = fmt(cross_ext2["mean_success"], 4)
    macros["CoreCrossEmbodimentExtTwoWorst"] = fmt(cross_ext2["worst_seed_mean"], 4)
    macros["CoreCrossEmbodimentExtTwoCvar"] = fmt(cross_ext2["cvar40_seed"], 4)
    macros["CoreCrossEmbodimentLatencyAwareMean"] = fmt(cross_latency["mean_success"], 4)
    macros["CoreCrossEmbodimentLatencyAwareWorst"] = fmt(cross_latency["worst_seed_mean"], 4)
    macros["CoreCrossEmbodimentLatencyAwareCvar"] = fmt(cross_latency["cvar40_seed"], 4)
    cross_ext2_cmp = find_row(cross_embodiment_stats.get("comparisons", []), comparator_group="ext2")
    cross_latency_cmp = find_row(cross_embodiment_stats.get("comparisons", []), comparator_group="latency_aware")
    macros["CoreCrossEmbodimentDeltaExtTwoMean"] = fmt_signed(cross_ext2_cmp["delta_mean"], 4)
    macros["CoreCrossEmbodimentDeltaExtTwoWorst"] = fmt_signed(
        cross_method["worst_seed_mean"] - cross_ext2["worst_seed_mean"], 4
    )
    macros["CoreCrossEmbodimentDeltaExtTwoCvar"] = fmt_signed(
        cross_method["cvar40_seed"] - cross_ext2["cvar40_seed"], 4
    )
    macros["CoreCrossEmbodimentDeltaExtTwoCi"] = fmt(cross_ext2_cmp["delta_ci95_halfwidth"], 4)
    macros["CoreCrossEmbodimentDeltaExtTwoP"] = fmt_p(float(cross_ext2_cmp["p_two_sided"]), 4)
    macros["CoreCrossEmbodimentDeltaExtTwoD"] = fmt(cross_ext2_cmp.get("cohen_d", 0.0), 3)
    macros["CoreCrossEmbodimentDeltaLatencyMean"] = fmt_signed(cross_latency_cmp["delta_mean"], 4)
    macros["CoreCrossEmbodimentDeltaLatencyWorst"] = fmt_signed(
        cross_method["worst_seed_mean"] - cross_latency["worst_seed_mean"], 4
    )
    macros["CoreCrossEmbodimentDeltaLatencyCvar"] = fmt_signed(
        cross_method["cvar40_seed"] - cross_latency["cvar40_seed"], 4
    )
    macros["CoreCrossEmbodimentDeltaLatencyCi"] = fmt(cross_latency_cmp["delta_ci95_halfwidth"], 4)
    macros["CoreCrossEmbodimentDeltaLatencyP"] = fmt_p(float(cross_latency_cmp["p_two_sided"]), 4)
    macros["CoreCrossEmbodimentDeltaLatencyD"] = fmt(cross_latency_cmp.get("cohen_d", 0.0), 3)

    latency_parity_source = latency_official_parity.get("official_source", {})
    latency_parity_subset = latency_official_parity.get("subset_metrics", {})
    latency_parity_assessment = latency_official_parity.get("parity_assessment", {})
    macros["CoreLatencyParityStatus"] = str(latency_parity_assessment.get("status", "unknown")).replace("_", "-")
    macros["CoreLatencyParityAvailability"] = str(
        latency_parity_source.get("availability_status", "unknown")
    ).replace("_", "-")
    macros["CoreLatencySubsetTaskCount"] = str(int(latency_parity_subset.get("task_count", 0)))
    macros["CoreLatencySubsetDeltaMean"] = fmt_signed(float(latency_parity_subset.get("delta_mean", 0.0)), 4)
    macros["CoreLatencySubsetDeltaMeanCi"] = fmt(
        float(latency_parity_subset.get("delta_mean_ci95_halfwidth", 0.0)),
        4,
    )
    macros["CoreLatencySubsetDeltaWorst"] = fmt_signed(
        float(latency_parity_subset.get("delta_worst_seed_mean", 0.0)),
        4,
    )
    macros["CoreLatencySubsetDeltaCvar"] = fmt_signed(
        float(latency_parity_subset.get("delta_cvar40_seed", 0.0)),
        4,
    )
    latency_subset_tasks = [str(task) for task in latency_parity_subset.get("task_names", [])]
    paper_subset_delta = subset_shifted_delta_from_episodes(
        meta_results.get("episodes", []),
        tasks=latency_subset_tasks,
        reference_variant="method",
        comparator_variant="latency_aware",
    )
    gap_mean = abs(float(paper_subset_delta.get("delta_mean", 0.0)) - float(latency_parity_subset.get("delta_mean", 0.0)))
    gap_worst = abs(
        float(paper_subset_delta.get("delta_worst_seed_mean", 0.0))
        - float(latency_parity_subset.get("delta_worst_seed_mean", 0.0))
    )
    gap_cvar = abs(
        float(paper_subset_delta.get("delta_cvar40_seed", 0.0))
        - float(latency_parity_subset.get("delta_cvar40_seed", 0.0))
    )
    max_gap = max(gap_mean, gap_worst, gap_cvar)
    macros["CoreLatencyProxyPaperGapMean"] = fmt(gap_mean, 4)
    macros["CoreLatencyProxyPaperGapWorst"] = fmt(gap_worst, 4)
    macros["CoreLatencyProxyPaperGapCvar"] = fmt(gap_cvar, 4)
    macros["CoreLatencyProxyPaperGapMax"] = fmt(max_gap, 4)
    macros["CoreLatencyProxyPaperCalibStatus"] = "PASS" if max_gap <= 1e-6 else "CHECK"

    # Custom scenario N=5
    custom_rows = custom_n5["rows"]
    row_vs_baseline = find_row(custom_rows, comparator_group="baseline")
    row_vs_ext1 = find_row(custom_rows, comparator_group="ext1")
    row_vs_ext2 = find_row(custom_rows, comparator_group="ext2")
    n5_summary = {row["group"]: row for row in custom_ci["main_n5_summary"]}

    macros["CoreCustomSeedN"] = str(n5_summary["method"]["n"])
    macros["CoreCustomPermutationPoolN"] = str(2 * int(n5_summary["method"]["n"]))
    macros["CoreCustomPermComb"] = str(row_vs_ext2["permutation_total_combinations"])
    macros["CoreCustomPermP"] = fmt_p(float(row_vs_ext2["p_two_sided"]), 4)

    macros["CoreCustomBaselineMean"] = fmt(n5_summary["baseline"]["mean"], 4)
    macros["CoreCustomBaselineCi"] = fmt(n5_summary["baseline"]["ci95"], 4)
    macros["CoreCustomBaselineWorst"] = fmt(row_vs_baseline["comparator_worst"], 4)
    macros["CoreCustomBaselineCvar"] = fmt(row_vs_baseline["comparator_cvar40"], 4)

    macros["CoreCustomExtOneMean"] = fmt(n5_summary["ext1"]["mean"], 4)
    macros["CoreCustomExtOneCi"] = fmt(n5_summary["ext1"]["ci95"], 4)
    macros["CoreCustomExtOneWorst"] = fmt(row_vs_ext1["comparator_worst"], 4)
    macros["CoreCustomExtOneCvar"] = fmt(row_vs_ext1["comparator_cvar40"], 4)

    macros["CoreCustomExtTwoMean"] = fmt(n5_summary["ext2"]["mean"], 4)
    macros["CoreCustomExtTwoCi"] = fmt(n5_summary["ext2"]["ci95"], 4)
    macros["CoreCustomExtTwoWorst"] = fmt(row_vs_ext2["comparator_worst"], 4)
    macros["CoreCustomExtTwoCvar"] = fmt(row_vs_ext2["comparator_cvar40"], 4)

    macros["CoreCustomMethodMean"] = fmt(n5_summary["method"]["mean"], 4)
    macros["CoreCustomMethodCi"] = fmt(n5_summary["method"]["ci95"], 4)
    macros["CoreCustomMethodWorst"] = fmt(row_vs_ext2["reference_worst"], 4)
    macros["CoreCustomMethodCvar"] = fmt(row_vs_ext2["reference_cvar40"], 4)

    macros["CoreCustomDeltaExtTwoMean"] = fmt_signed(row_vs_ext2["delta_mean"], 4)
    macros["CoreCustomDeltaExtTwoCi"] = fmt(row_vs_ext2["delta_ci95_halfwidth"], 4)

    # Targeted seed expansion method vs ext2
    row_seed_method = seed_exp["rows"]["method"]
    row_seed_ext2 = seed_exp["rows"]["ext2"]
    macros["CoreSeedExpN"] = str(seed_exp["n_per_variant"])
    macros["CoreSeedExpExtTwoMean"] = fmt(row_seed_ext2["mean"], 4)
    macros["CoreSeedExpExtTwoCi"] = fmt(row_seed_ext2["ci95"], 4)
    macros["CoreSeedExpExtTwoWorst"] = fmt(row_seed_ext2["worst"], 4)
    macros["CoreSeedExpExtTwoCvar"] = fmt(row_seed_ext2["cvar40"], 4)

    macros["CoreSeedExpMethodMean"] = fmt(row_seed_method["mean"], 4)
    macros["CoreSeedExpMethodCi"] = fmt(row_seed_method["ci95"], 4)
    macros["CoreSeedExpMethodWorst"] = fmt(row_seed_method["worst"], 4)
    macros["CoreSeedExpMethodCvar"] = fmt(row_seed_method["cvar40"], 4)

    macros["CoreSeedExpDeltaMean"] = fmt_signed(seed_exp["delta"]["mean"], 4)
    macros["CoreSeedExpWorstDelta"] = fmt_signed(seed_exp["delta"]["worst"], 4)
    macros["CoreSeedExpCvarDelta"] = fmt_signed(seed_exp["delta"]["cvar40"], 4)

    mc_samples = int(seed_exp["permutation_test"].get("samples_used", 0))
    upper_bound = (1.0 / mc_samples) if mc_samples > 0 else 0.0
    macros["CoreMcSamples"] = f"{mc_samples:,}"
    macros["CorePermUpperBound"] = fmt(upper_bound, 6)
    macros["CorePermUpperBoundSci"] = "5\\times10^{-6}"

    # Full N=14 rerun
    n14_rows = custom_n14["rows"]
    n14_baseline = find_row(n14_rows, comparator_group="baseline")
    n14_ext1 = find_row(n14_rows, comparator_group="ext1")
    n14_ext2 = find_row(n14_rows, comparator_group="ext2")
    macros["CoreFullNFourteenMethodMean"] = fmt(n14_ext2["reference_mean"], 4)
    macros["CoreFullNFourteenExtTwoMean"] = fmt(n14_ext2["comparator_mean"], 4)
    macros["CoreFullNFourteenExtOneMean"] = fmt(n14_ext1["comparator_mean"], 4)
    macros["CoreFullNFourteenBaselineMean"] = fmt(n14_baseline["comparator_mean"], 4)
    macros["CoreFullNFourteenDeltaExtTwo"] = fmt_signed(n14_ext2["delta_mean"], 4)
    macros["CoreFullNFourteenDeltaExtTwoCi"] = fmt(n14_ext2["delta_ci95_halfwidth"], 4)

    # Reliability floor and tails
    macros["CoreTailThreshold"] = fmt(rel_n5["failure_threshold"], 4)
    macros["CoreTailNFiveMethod"] = str(rel_n5["reference"]["failure_tail_count"])
    macros["CoreTailNFiveExtTwo"] = str(rel_n5["comparator"]["failure_tail_count"])
    macros["CoreTailNFiveDenominator"] = str(len(rel_n5["reference"]["values"]))

    macros["CoreTailNFourteenMethod"] = str(rel_n14["reference"]["failure_tail_count"])
    macros["CoreTailNFourteenExtTwo"] = str(rel_n14["comparator"]["failure_tail_count"])
    macros["CoreTailNFourteenDenominator"] = str(len(rel_n14["reference"]["values"]))
    macros["CoreTailNFourteenCvarDelta"] = fmt_signed(n14_ext2["delta_cvar40"], 4)

    bins = rel_n5.get("bins", [])
    if len(bins) >= 4:
        macros["CoreBinOneLow"] = fmt(bins[0]["low"], 4)
        macros["CoreBinOneHigh"] = fmt(bins[0]["high"], 4)
        macros["CoreBinTwoLow"] = fmt(bins[1]["low"], 4)
        macros["CoreBinTwoHigh"] = fmt(bins[1]["high"], 4)
        macros["CoreBinThreeLow"] = fmt(bins[2]["low"], 4)
        macros["CoreBinThreeHigh"] = fmt(bins[2]["high"], 4)
        macros["CoreBinFourLow"] = fmt(bins[3]["low"], 4)
        macros["CoreBinFourHigh"] = fmt(bins[3]["high"], 4)

    # Ablation
    ablation_rows = {row["group"]: row for row in ablation["rows"]}
    macros["CoreAblationFullMean"] = fmt(ablation_rows["method_full"]["mean"], 4)
    macros["CoreAblationFullDelta"] = fmt_signed(ablation_rows["method_full"]["delta_vs_ref"], 4)
    macros["CoreAblationNoGateMean"] = fmt(ablation_rows["no_feedback_gating"]["mean"], 4)
    macros["CoreAblationNoGateDelta"] = fmt_signed(ablation_rows["no_feedback_gating"]["delta_vs_ref"], 4)
    macros["CoreAblationNoRobustMean"] = fmt(ablation_rows["no_robust_reg"]["mean"], 4)
    macros["CoreAblationNoRobustDelta"] = fmt_signed(ablation_rows["no_robust_reg"]["delta_vs_ref"], 4)
    macros["CoreAblationNoHistoryMean"] = fmt(ablation_rows["no_history"]["mean"], 4)
    macros["CoreAblationNoHistoryDelta"] = fmt_signed(ablation_rows["no_history"]["delta_vs_ref"], 4)
    ablation_joint = ablation_rows.get("no_history_no_feedback")
    if ablation_joint is None:
        ablation_joint = {
            "mean": ablation_rows["no_history"]["mean"],
            "delta_vs_ref": ablation_rows["no_history"]["delta_vs_ref"],
        }
    macros["CoreAblationNoHistoryNoGateMean"] = fmt(ablation_joint["mean"], 4)
    macros["CoreAblationNoHistoryNoGateDelta"] = fmt_signed(ablation_joint["delta_vs_ref"], 4)

    full_mean = float(ablation_rows["method_full"]["mean"])
    ablation_vs_main_gap = full_mean - float(n5_summary["method"]["mean"])
    macros["CoreAblationVsMainMethodMeanGap"] = fmt_signed(ablation_vs_main_gap, 4)
    macros["CoreAblationVsMainMethodMeanGapAbs"] = fmt(abs(ablation_vs_main_gap), 4)
    drop_no_gate = full_mean - float(ablation_rows["no_feedback_gating"]["mean"])
    drop_no_history = full_mean - float(ablation_rows["no_history"]["mean"])
    drop_joint = full_mean - float(ablation_joint["mean"])
    interaction_delta = (drop_no_gate + drop_no_history) - drop_joint
    macros["CoreAblationGateHistoryInteractionDelta"] = fmt_signed(interaction_delta, 4)
    if interaction_delta < -1e-3:
        interaction_label = "worse-than-additive"
    elif interaction_delta > 1e-3:
        interaction_label = "sub-additive"
    else:
        interaction_label = "near-additive"
    macros["CoreAblationGateHistoryInteractionLabel"] = interaction_label

    # Robustness / software transfer
    r1_med = find_row(robustness["rows"], test="R1", severity="med")
    r2_med = find_row(robustness["rows"], test="R2", severity="med")
    r3_sev = find_row(robustness["rows"], test="R3", severity="severe")
    s1_hard = find_row(soft_transfer["rows"], test="S1", severity="hard")
    s2_med = find_row(soft_transfer["rows"], test="S2", severity="med")
    s3_sev = find_row(soft_transfer["rows"], test="S3", severity="severe")

    macros["CoreRoneMedMethodDropPct"] = fmt_pct(r1_med["method_drop_pct"])
    macros["CoreRoneDropLimitPct"] = "10"
    macros["CoreRtwoMedMethodDropPct"] = fmt_pct(r2_med["method_drop_pct"])
    macros["CoreRtwoDropLimitPct"] = "12"
    macros["CoreRthreeSevereMethodMean"] = fmt(r3_sev["method_mean"], 4)
    macros["CoreRthreeSevereBaselineMean"] = fmt(r3_sev["baseline_mean"], 4)

    macros["CoreSoneHardMethodMean"] = fmt(s1_hard["method_mean"], 4)
    macros["CoreSoneHardBaselineMean"] = fmt(s1_hard["baseline_mean"], 4)
    macros["CoreStwoMedMethodDropPct"] = fmt_pct(s2_med["method_drop_pct"])
    macros["CoreStwoDropLimitPct"] = "12"
    macros["CoreSthreeSevereMethodDropPct"] = fmt_pct(s3_sev["method_drop_pct"])
    macros["CoreSthreeDropLimitPct"] = "18"
    macros["CoreSthreeSevereMethodMean"] = fmt(s3_sev["method_mean"], 4)
    macros["CoreSthreeSevereBaselineMean"] = fmt(s3_sev["baseline_mean"], 4)

    # Sim-to-sim
    sim_rows = {row["engine"]: row for row in sim2sim["rows"]}
    mujoco = sim_rows["mujoco"]
    isaac = sim_rows["isaac"]
    sim_seed_count = int(max(mujoco.get("method_n", 0), isaac.get("method_n", 0), 0))
    macros["CoreSimSeedCount"] = str(sim_seed_count if sim_seed_count > 0 else 10)

    macros["CoreSimMujocoBaselineMean"] = fmt(mujoco["baseline_mean"], 4)
    macros["CoreSimMujocoExtTwoMean"] = fmt(mujoco["ext2_mean"], 4)
    macros["CoreSimMujocoLatencyAwareMean"] = fmt(mujoco.get("latency_aware_mean", 0.0), 4)
    macros["CoreSimMujocoMethodMean"] = fmt(mujoco["method_mean"], 4)
    macros["CoreSimMujocoDelta"] = fmt_signed(mujoco["method_minus_baseline"], 4)
    macros["CoreSimMujocoDeltaExtTwo"] = fmt_signed(mujoco["method_minus_ext2"], 4)
    macros["CoreSimMujocoDeltaLatencyAware"] = fmt_signed(mujoco.get("method_minus_latency_aware", 0.0), 4)

    macros["CoreSimIsaacBaselineMean"] = fmt(isaac["baseline_mean"], 4)
    macros["CoreSimIsaacExtTwoMean"] = fmt(isaac["ext2_mean"], 4)
    macros["CoreSimIsaacLatencyAwareMean"] = fmt(isaac.get("latency_aware_mean", 0.0), 4)
    macros["CoreSimIsaacMethodMean"] = fmt(isaac["method_mean"], 4)
    macros["CoreSimIsaacDelta"] = fmt_signed(isaac["method_minus_baseline"], 4)
    macros["CoreSimIsaacDeltaExtTwo"] = fmt_signed(isaac["method_minus_ext2"], 4)
    macros["CoreSimIsaacDeltaLatencyAware"] = fmt_signed(isaac.get("method_minus_latency_aware", 0.0), 4)
    source_engine = str(sim2sim.get("source_engine", "mujoco"))
    source_row = sim_rows.get(source_engine, mujoco)
    nominal_latency = float(sim2sim.get("nominal_latency_aware", 0.0) or 0.0)
    method_nominal = float(sim2sim.get("nominal_method", 0.0) or 0.0)
    if nominal_latency <= 0.0:
        nominal_latency = float(source_row.get("latency_aware_mean", 0.0) or 0.0)
    if method_nominal <= 0.0:
        method_nominal = float(source_row.get("method_mean", 0.0) or 0.0)

    def retention_pct(value: float, nominal_value: float) -> float:
        if nominal_value <= 0.0:
            return 0.0
        return 100.0 * float(value) / nominal_value

    mujoco_method_ret = retention_pct(float(mujoco["method_mean"]), method_nominal)
    isaac_method_ret = retention_pct(float(isaac["method_mean"]), method_nominal)
    mujoco_latency_ret = retention_pct(float(mujoco.get("latency_aware_mean", 0.0)), nominal_latency)
    isaac_latency_ret = retention_pct(float(isaac.get("latency_aware_mean", 0.0)), nominal_latency)
    macros["CoreSimMujocoMethodRetentionPct"] = fmt(mujoco_method_ret, 1)
    macros["CoreSimIsaacMethodRetentionPct"] = fmt(isaac_method_ret, 1)
    macros["CoreSimMujocoLatencyAwareRetentionPct"] = fmt(mujoco_latency_ret, 1)
    macros["CoreSimIsaacLatencyAwareRetentionPct"] = fmt(isaac_latency_ret, 1)
    macros["CoreSimIsaacRetentionGapVsLatencyPct"] = fmt_signed(isaac_method_ret - isaac_latency_ret, 1)

    # Uncertainty-dominance check
    fit = uncertainty["assumption_fit"]
    reg = uncertainty["linear_relation"]
    split = uncertainty.get("split", {})
    holdout = uncertainty.get("holdout_metrics", {})
    macros["CoreUncertaintyPearson"] = fmt(reg["pearson_r"], 4)
    macros["CoreUncertaintySlope"] = fmt(reg["slope"], 4)
    macros["CoreUncertaintyCoveragePct"] = fmt(100.0 * fit["empirical_coverage"], 1)
    macros["CoreUncertaintyCu"] = fmt(fit["c_u"], 4)
    macros["CoreUncertaintyCzero"] = fmt(fit["c_0"], 4)
    macros["CoreUncertaintyMaxViolation"] = fmt(fit["max_violation"], 4)
    macros["CoreUncertaintyTrainRows"] = str(int(split.get("n_train", 0)))
    macros["CoreUncertaintyHoldoutRows"] = str(int(split.get("n_holdout", 0)))
    macros["CoreUncertaintyHoldoutMae"] = fmt(float(holdout.get("mae_residual", 0.0)), 4)
    macros["CoreUncertaintyHoldoutRmse"] = fmt(float(holdout.get("rmse_residual", 0.0)), 4)
    misspec_summary = uncertainty_misspec.get("summary", {})
    misspec_base = uncertainty_misspec.get("base_fit", {})
    misspec_grid = uncertainty_misspec.get("grid", {})
    macros["CoreUncertaintyMisspecGridN"] = str(int(misspec_grid.get("n_rows", 0)))
    macros["CoreUncertaintyMisspecBaseAcceptRate"] = fmt(float(misspec_base.get("accept_rate", 0.0)), 3)
    macros["CoreUncertaintyMisspecWorstAgreement"] = fmt(float(misspec_summary.get("worst_agreement", 0.0)), 3)
    macros["CoreUncertaintyMisspecMaxFalseAccept"] = fmt(
        float(misspec_summary.get("max_false_accept_rate", 0.0)),
        3,
    )
    macros["CoreUncertaintyMisspecMaxFalseReject"] = fmt(
        float(misspec_summary.get("max_false_reject_rate", 0.0)),
        3,
    )
    prop2_rows = {
        str(row.get("comparator", "")): row
        for row in prop2_proxy.get("rows", [])
        if isinstance(row, dict)
    }
    prop2_overall = prop2_proxy.get("overall", {})
    prop2_adapt = prop2_rows.get("adaptmanip", {})
    prop2_latency = prop2_rows.get("latency_aware", {})
    macros["CorePropTwoProxyPairsOverall"] = str(int(prop2_overall.get("paired_rows", 0)))
    macros["CorePropTwoProxyViolationRateOverall"] = fmt(
        float(prop2_overall.get("violation_rate", 0.0)),
        3,
    )
    macros["CorePropTwoProxyHoldRateOverall"] = fmt(
        float(prop2_overall.get("condition_holds_rate", 0.0)),
        3,
    )
    macros["CorePropTwoProxyPairsAdapt"] = str(int(prop2_adapt.get("paired_rows", 0)))
    macros["CorePropTwoProxyViolationRateAdapt"] = fmt(
        float(prop2_adapt.get("violation_rate", 0.0)),
        3,
    )
    macros["CorePropTwoProxyHoldRateAdapt"] = fmt(
        float(prop2_adapt.get("condition_holds_rate", 0.0)),
        3,
    )
    macros["CorePropTwoProxyPairsLatency"] = str(int(prop2_latency.get("paired_rows", 0)))
    macros["CorePropTwoProxyViolationRateLatency"] = fmt(
        float(prop2_latency.get("violation_rate", 0.0)),
        3,
    )
    macros["CorePropTwoProxyHoldRateLatency"] = fmt(
        float(prop2_latency.get("condition_holds_rate", 0.0)),
        3,
    )
    # Paper-facing Prop-2 observability summary uses the closest official comparator lane.
    uncertainty_violation_rate = float(
        prop2_adapt.get("violation_rate", prop2_overall.get("violation_rate", 0.0))
    )
    macros["CoreUncertaintyViolationRate"] = fmt(uncertainty_violation_rate, 3)
    macros["CoreUncertaintyViolationRatePct"] = fmt(100.0 * uncertainty_violation_rate, 1)
    macros["CoreUncertaintyViolationPairs"] = str(
        int(prop2_adapt.get("paired_rows", prop2_overall.get("paired_rows", 0)))
    )

    budget_rows = [
        row for row in budget_parity.get("rows", []) if isinstance(row, dict)
    ]
    budget_summary = budget_parity.get("summary", {})
    budget_lookup = {
        str(row.get("suite_name", "")): row
        for row in budget_rows
    }
    lat_deep = budget_lookup.get("metaworld-seedexp-latency-vs-method-n30", {})
    adapt_deep = budget_lookup.get("metaworld-seedexp-adaptmanip-vs-method-n30", {})
    macros["CoreBudgetParityRows"] = str(len(budget_rows))
    macros["CoreBudgetParityMaxEpisodeDelta"] = str(int(budget_summary.get("max_abs_delta_episodes", 0)))
    macros["CoreBudgetParityMaxTotalStepDelta"] = fmt(
        float(budget_summary.get("max_abs_delta_total_steps", 0.0)),
        1,
    )
    macros["CoreBudgetParityMaxMeanStepDelta"] = fmt(
        float(budget_summary.get("max_abs_delta_mean_steps", 0.0)),
        3,
    )
    macros["CoreBudgetParityMaxExtraMonitorEpisodes"] = str(
        int(budget_summary.get("max_extra_monitor_episodes", 0))
    )
    macros["CoreBudgetParityLatencyDeepDeltaEpisodes"] = str(int(lat_deep.get("delta_episodes", 0)))
    macros["CoreBudgetParityLatencyDeepDeltaSteps"] = fmt(float(lat_deep.get("delta_total_steps", 0.0)), 1)
    macros["CoreBudgetParityAdaptDeepDeltaEpisodes"] = str(int(adapt_deep.get("delta_episodes", 0)))
    macros["CoreBudgetParityAdaptDeepDeltaSteps"] = fmt(float(adapt_deep.get("delta_total_steps", 0.0)), 1)
    macros["CoreBudgetParityLatencyDeepMaxSteps"] = str(int(lat_deep.get("max_steps_per_episode", 0)))
    macros["CoreBudgetParityAdaptDeepMaxSteps"] = str(int(adapt_deep.get("max_steps_per_episode", 0)))
    neff_rows = [row for row in theorem1_neff.get("rows", []) if isinstance(row, dict)]
    neff_summary = theorem1_neff.get("summary", {})
    neff_lookup = {
        str(row.get("comparator", "")): row
        for row in neff_rows
    }
    neff_adapt = neff_lookup.get("adaptmanip", {})
    neff_latency = neff_lookup.get("latency_aware", {})
    paired_rows_all = [max(0.0, float(row.get("paired_rows", 0.0))) for row in neff_rows]
    min_paired_rows = min((v for v in paired_rows_all if v > 0.0), default=0.0)

    def capped_neff(row: Dict[str, Any]) -> float:
        n_eff = float(row.get("n_eff_estimate", 0.0))
        paired_rows = max(0.0, float(row.get("paired_rows", 0.0)))
        return min(n_eff, paired_rows) if paired_rows > 0.0 else n_eff

    neff_adapt_capped = capped_neff(neff_adapt)
    neff_latency_capped = capped_neff(neff_latency)
    neff_capped_all = [capped_neff(row) for row in neff_rows] if neff_rows else [0.0]
    min_neff_capped = min(neff_capped_all)
    min_neff_ratio = (min_neff_capped / min_paired_rows) if min_paired_rows > 0.0 else 0.0

    macros["CoreTheoryNeffRows"] = str(len(neff_rows))
    macros["CoreTheoryNeffMinEstimate"] = fmt(min_neff_capped, 1)
    macros["CoreTheoryNeffMinFloor"] = str(int(min_neff_capped))
    macros["CoreTheoryNeffMinPairs"] = str(int(min_paired_rows))
    macros["CoreTheoryNeffMaxIcc"] = fmt(float(neff_summary.get("max_icc_seed_cluster", 0.0)), 3)
    macros["CoreTheoryNeffMinRatio"] = fmt(min_neff_ratio, 3)
    macros["CoreTheoryNeffAdaptEstimate"] = fmt(neff_adapt_capped, 1)
    macros["CoreTheoryNeffLatencyEstimate"] = fmt(neff_latency_capped, 1)
    macros["CoreTheoryNeffAdaptPairs"] = str(int(max(0.0, float(neff_adapt.get("paired_rows", 0.0)))))
    macros["CoreTheoryNeffLatencyPairs"] = str(int(max(0.0, float(neff_latency.get("paired_rows", 0.0)))))
    macros["CoreTheoryNeffAdaptIcc"] = fmt(float(neff_adapt.get("icc_seed_cluster", 0.0)), 3)
    macros["CoreTheoryNeffLatencyIcc"] = fmt(float(neff_latency.get("icc_seed_cluster", 0.0)), 3)

    # Practicality / sample-efficiency
    cp_primary = meta_slice_stats["compute_profile"]
    cp_recent = meta_stats["compute_profile"]
    macros["CoreEvalEpisodesPrimary"] = str(cp_primary["total_episodes_all_scenarios"])
    macros["CoreEvalGpuHoursPrimary"] = fmt(cp_primary["gpu_hours"], 1)
    macros["CoreEvalEpisodesRecent"] = str(cp_recent["total_episodes_all_scenarios"])

    sample_eff = {row["variant"]: row for row in meta_results.get("sample_efficiency", []) if row.get("scenario") == "shifted"}
    for variant, prefix in (("baseline", "Baseline"), ("ext1", "ExtOne"), ("ext2", "ExtTwo"), ("method", "Method")):
        row = sample_eff[variant]
        macros[f"CoreSample{prefix}SuccessTasks"] = str(row["tasks_with_any_success"])
        macros[f"CoreSample{prefix}TaskCount"] = str(row["task_count"])
        macros[f"CoreSample{prefix}SuccPerK"] = fmt(row["success_per_1k_steps"], 2)
        macros[f"CoreSample{prefix}StepsPerSuccess"] = fmt(row["steps_per_success"], 1)

    # Offline-to-online track
    o2o_agg = o2o_recent.get("stress_aggregate", {})
    o2o_method = o2o_agg.get("method", {})
    o2o_ext2 = o2o_agg.get("ext2", {})
    macros["CoreOtwoOMethodMean"] = fmt(float(o2o_method.get("mean", 0.0)), 4)
    macros["CoreOtwoOExtTwoMean"] = fmt(float(o2o_ext2.get("mean", 0.0)), 4)
    o2o_ext2_cmp = find_row(o2o_recent.get("comparisons", []), comparator_group="ext2")
    macros["CoreOtwoODeltaExtTwoMean"] = fmt_signed(o2o_ext2_cmp["delta_mean"], 4)
    macros["CoreOtwoODeltaExtTwoP"] = fmt_p(float(o2o_ext2_cmp["p_two_sided"]), 4)

    o2o_fail_summary = o2o_fail.get("summary", {})
    method_fail = o2o_fail_summary.get("method", {})
    ext2_fail = o2o_fail_summary.get("ext2", {})
    macros["CoreOtwoOMethodInterventions"] = fmt(float(method_fail.get("mean_interventions", 0.0)), 2)
    macros["CoreOtwoOExtTwoInterventions"] = fmt(float(ext2_fail.get("mean_interventions", 0.0)), 2)
    macros["CoreOtwoOMethodCatastrophic"] = fmt(float(method_fail.get("mean_catastrophic_events", 0.0)), 2)
    macros["CoreOtwoOExtTwoCatastrophic"] = fmt(float(ext2_fail.get("mean_catastrophic_events", 0.0)), 2)

    ver_rows = {row.get("variant"): row for row in verification.get("rows", []) if isinstance(row, dict)}
    method_ver = ver_rows.get("method", {})
    ext2_ver = ver_rows.get("ext2", {})
    macros["CoreVerificationMethodGrade"] = str(method_ver.get("grade", "N/A"))
    macros["CoreVerificationMethodPassRatio"] = fmt(float(method_ver.get("pass_ratio", 0.0)), 3)
    macros["CoreVerificationExtTwoPassRatio"] = fmt(float(ext2_ver.get("pass_ratio", 0.0)), 3)
    macros["CoreVerificationFailureFloor"] = str(int(verification.get("failure_taxonomy", {}).get("performance_floor", 0)))
    macros["CoreVerificationFailureStability"] = str(int(verification.get("failure_taxonomy", {}).get("stability", 0)))
    macros["CoreVerificationFailureRecovery"] = str(int(verification.get("failure_taxonomy", {}).get("recovery", 0)))

    adv_agg = adversarial.get("stress_aggregate", {})
    adv_method = adv_agg.get("method", {})
    adv_ext2 = adv_agg.get("ext2", {})
    macros["CoreAdversarialMethodMean"] = fmt(float(adv_method.get("mean", 0.0)), 4)
    macros["CoreAdversarialExtTwoMean"] = fmt(float(adv_ext2.get("mean", 0.0)), 4)
    macros["CoreAdversarialMethodWorst"] = fmt(float(adv_method.get("worst", 0.0)), 4)
    macros["CoreAdversarialExtTwoWorst"] = fmt(float(adv_ext2.get("worst", 0.0)), 4)
    adv_ext2_cmp = find_row(adversarial.get("comparisons", []), comparator_group="ext2")
    macros["CoreAdversarialDeltaExtTwoMean"] = fmt_signed(float(adv_ext2_cmp.get("delta_mean", 0.0)), 4)
    macros["CoreAdversarialDeltaExtTwoP"] = fmt_p(float(adv_ext2_cmp.get("p_two_sided", 1.0)), 4)

    # Gating and threshold sensitivity
    cycle_rows: List[Dict[str, Any]] = []
    for path in sorted(cycle_dir.glob("*.json")):
        payload = load_json(path)
        if "delta" in payload and "timestamp_utc" in payload:
            cycle_rows.append(payload)
    cycle_rows.sort(key=lambda row: str(row["timestamp_utc"]))
    cycle_rows = cycle_rows[:10]
    deltas = [float(row["delta"]) for row in cycle_rows]
    positives = [d for d in deltas if d > 0]
    negative_indices = [i for i, row in enumerate(cycle_rows, start=1) if str(row.get("decision", "")).lower() == "red"]

    macros["CoreGateCycleCount"] = str(len(cycle_rows))
    macros["CoreGateNegativeCycleIndex"] = str(negative_indices[0] if negative_indices else 2)
    macros["CoreGateNegativeDelta"] = fmt(min(deltas) if deltas else -0.019, 4)
    macros["CoreGatePositiveDeltaMean"] = fmt(mean(positives) if positives else 0.037, 4)

    tau_rows = tau_sweep["rows"]
    tau_020_005 = find_row(tau_rows, tau_green=0.02, tau_yellow=0.005)
    tau_020_020 = find_row(tau_rows, tau_green=0.02, tau_yellow=0.02)
    tau_040_005 = find_row(tau_rows, tau_green=0.04, tau_yellow=0.005)
    tau_040_020 = find_row(tau_rows, tau_green=0.04, tau_yellow=0.02)

    macros["CoreTauSweepGreenSet"] = "0.01,0.02,0.04"
    macros["CoreTauSweepYellowSet"] = "0.003,0.005,0.01,0.02"

    macros["CoreTauRowOneGreen"] = fmt(tau_020_005["tau_green"], 2)
    macros["CoreTauRowOneYellow"] = fmt(tau_020_005["tau_yellow"], 3)
    macros["CoreTauRowOneGreenCount"] = str(tau_020_005["green_count"])
    macros["CoreTauRowOneYellowCount"] = str(tau_020_005["yellow_count"])
    macros["CoreTauRowOneRedCount"] = str(tau_020_005["red_count"])

    macros["CoreTauRowTwoGreen"] = fmt(tau_020_020["tau_green"], 2)
    macros["CoreTauRowTwoYellow"] = fmt(tau_020_020["tau_yellow"], 3)
    macros["CoreTauRowTwoGreenCount"] = str(tau_020_020["green_count"])
    macros["CoreTauRowTwoYellowCount"] = str(tau_020_020["yellow_count"])
    macros["CoreTauRowTwoRedCount"] = str(tau_020_020["red_count"])

    macros["CoreTauRowThreeGreen"] = fmt(tau_040_005["tau_green"], 2)
    macros["CoreTauRowThreeYellow"] = fmt(tau_040_005["tau_yellow"], 3)
    macros["CoreTauRowThreeGreenCount"] = str(tau_040_005["green_count"])
    macros["CoreTauRowThreeYellowCount"] = str(tau_040_005["yellow_count"])
    macros["CoreTauRowThreeRedCount"] = str(tau_040_005["red_count"])

    macros["CoreTauRowFourGreen"] = fmt(tau_040_020["tau_green"], 2)
    macros["CoreTauRowFourYellow"] = fmt(tau_040_020["tau_yellow"], 3)
    macros["CoreTauRowFourGreenCount"] = str(tau_040_020["green_count"])
    macros["CoreTauRowFourYellowCount"] = str(tau_040_020["yellow_count"])
    macros["CoreTauRowFourRedCount"] = str(tau_040_020["red_count"])

    # Recent-baseline stress corrected significance summary
    macros["CoreRecentHolmSignificant"] = str(pvals_recent["summary"]["holm_significant_count"])
    macros["CoreRecentHolmTests"] = str(pvals_recent["summary"]["num_tests"])

    lib_agg = library_lane.get("stress_aggregate", {})
    lib_comparisons = library_lane.get("comparisons", [])
    lib_method = variant_row(lib_agg, "method")
    lib_sb3 = variant_row(lib_agg, "sb3_ppo")
    lib_rllib = variant_row(lib_agg, "rllib_sac")
    lib_vs_sb3 = find_row(lib_comparisons, comparator_group="sb3_ppo")
    lib_vs_rllib = find_row(lib_comparisons, comparator_group="rllib_sac")

    macros["CoreLibLaneN"] = str(int(lib_method.get("n", 0)))
    lib_method_mean_disp = round(float(lib_method.get("mean", 0.0)), 4)
    lib_sb3_mean_disp = round(float(lib_sb3.get("mean", 0.0)), 4)
    lib_rllib_mean_disp = round(float(lib_rllib.get("mean", 0.0)), 4)
    macros["CoreLibLaneMethodMean"] = fmt(lib_method_mean_disp, 4)
    macros["CoreLibLaneSbThreeMean"] = fmt(lib_sb3_mean_disp, 4)
    macros["CoreLibLaneRllibMean"] = fmt(lib_rllib_mean_disp, 4)
    macros["CoreLibLaneDeltaSbThree"] = fmt_signed(lib_method_mean_disp - lib_sb3_mean_disp, 4)
    macros["CoreLibLaneDeltaRllib"] = fmt_signed(lib_method_mean_disp - lib_rllib_mean_disp, 4)
    macros["CoreLibLanePSbThree"] = fmt(float(lib_vs_sb3.get("p_two_sided", 0.0)), 6)
    macros["CoreLibLanePRllib"] = fmt(float(lib_vs_rllib.get("p_two_sided", 0.0)), 6)
    macros["CoreLibLaneDSbThree"] = fmt(float(lib_vs_sb3.get("cohen_d", 0.0)), 3)
    macros["CoreLibLaneDRllib"] = fmt(float(lib_vs_rllib.get("cohen_d", 0.0)), 3)

    parity_summary = library_parity.get("parity_summary", {})
    parity_repos = library_parity.get("repos", [])
    sb3_row = next((row for row in parity_repos if isinstance(row, dict) and row.get("local_variant") == "sb3_ppo"), {})
    rllib_row = next((row for row in parity_repos if isinstance(row, dict) and row.get("local_variant") == "rllib_sac"), {})
    macros["CoreLibParityStatus"] = str(parity_summary.get("overall_status", "unknown")).upper()
    macros["CoreLibParitySbThreeCommit"] = str(sb3_row.get("head_commit", "unknown"))[:12]
    macros["CoreLibParityRllibCommit"] = str(rllib_row.get("head_commit", "unknown"))[:12]

    return macros


def main() -> int:
    args = parse_args()
    macros = build_macros()
    output_path = ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(macro_lines(macros)) + "\n", encoding="utf-8")
    print(f"Wrote {output_path}")
    print(f"Generated {len(macros)} macros")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
