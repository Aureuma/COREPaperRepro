#!/usr/bin/env python3
"""Empirically check uncertainty-dominance proxy on benchmark run logs.

Assumption under check (design-rationale level):
    e <= c_u * U + c_0

where:
  - U is the uncertainty proxy (total scenario penalty),
  - e is empirical surrogate error proxy (|base_score - observed_score|).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import pathlib
import re
from typing import Dict, Iterable, List, Tuple


DEFAULT_LOG_DIRS = ",".join(
    [
        "output/corepaper_logs/experiments/external_latest",
        "output/corepaper_logs/experiments/robustness_latest",
        "output/corepaper_logs/experiments/software_transfer_latest",
        "output/corepaper_logs/experiments/sim2sim_latest",
    ]
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--logs-dirs",
        default=DEFAULT_LOG_DIRS,
        help="Comma-separated directories with run JSON files.",
    )
    parser.add_argument(
        "--output-json",
        default="output/corepaper_reports/ws5/uncertainty_dominance.json",
    )
    parser.add_argument(
        "--output-md",
        default="output/corepaper_reports/ws5/uncertainty_dominance.md",
    )
    parser.add_argument(
        "--coverage-quantile",
        type=float,
        default=0.95,
        help="Quantile used to fit conservative slope c_u from observed rows.",
    )
    parser.add_argument(
        "--train-fraction",
        type=float,
        default=0.8,
        help="Training fraction used for held-out calibration when seed split is unavailable.",
    )
    return parser.parse_args()


def mean(values: Iterable[float]) -> float:
    vals = list(values)
    return (sum(vals) / len(vals)) if vals else 0.0


def percentile(values: List[float], q: float) -> float:
    if not values:
        return 0.0
    q = max(0.0, min(1.0, q))
    xs = sorted(values)
    pos = q * (len(xs) - 1)
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return xs[lo]
    w = pos - lo
    return xs[lo] * (1.0 - w) + xs[hi] * w


def parse_logs_dirs(raw: str) -> List[pathlib.Path]:
    dirs = [pathlib.Path(item.strip()) for item in raw.split(",") if item.strip()]
    if not dirs:
        raise ValueError("No log directories specified.")
    return dirs


def extract_seed(run_id: str) -> int | None:
    match = re.search(r"-s(\d+)$", run_id)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None


def stable_hash(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:16], 16)


def load_rows(log_dirs: List[pathlib.Path]) -> List[Dict]:
    rows: List[Dict] = []
    for log_dir in log_dirs:
        for path in sorted(log_dir.glob("*.json")):
            if path.name == "suite_summary.json":
                continue
            blob = json.loads(path.read_text(encoding="utf-8"))
            payload = blob.get("metric_payload", {}) or {}
            comp = payload.get("score_components", {}) or {}
            if "base_score" not in comp or "total_penalty" not in comp:
                continue
            observed = payload.get("primary_metric")
            if observed is None:
                continue
            run_id = str(blob.get("run_id", path.stem))
            variant = str(payload.get("resolved_variant") or payload.get("variant") or "unknown")
            scenario = str(payload.get("scenario") or "unknown")
            base = float(comp["base_score"])
            u = abs(float(comp["total_penalty"]))
            e = abs(base - float(observed))
            rows.append(
                {
                    "run_id": run_id,
                    "suite_dir": str(log_dir),
                    "variant": variant,
                    "scenario": scenario,
                    "uncertainty_proxy": u,
                    "error_proxy": e,
                }
            )
    if not rows:
        raise ValueError("No compatible rows found in provided logs.")
    return rows


def linear_fit(x: List[float], y: List[float]) -> Tuple[float, float, float]:
    if len(x) != len(y) or not x:
        return 0.0, 0.0, 0.0
    mx = mean(x)
    my = mean(y)
    cov = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
    var_x = sum((xi - mx) ** 2 for xi in x)
    var_y = sum((yi - my) ** 2 for yi in y)
    slope = (cov / var_x) if var_x > 1e-12 else 0.0
    intercept = my - slope * mx
    corr = (cov / math.sqrt(var_x * var_y)) if (var_x > 1e-12 and var_y > 1e-12) else 0.0
    return slope, intercept, corr


def split_rows(rows: List[Dict], train_fraction: float) -> Tuple[List[Dict], List[Dict], str]:
    if not rows:
        return [], [], "empty"

    with_seed = [row for row in rows if extract_seed(str(row["run_id"])) is not None]
    if len(with_seed) >= max(10, len(rows) // 3):
        train: List[Dict] = []
        holdout: List[Dict] = []
        for row in rows:
            seed = extract_seed(str(row["run_id"]))
            if seed is None:
                bucket = stable_hash(str(row["run_id"])) % 2
                (train if bucket == 0 else holdout).append(row)
                continue
            (train if (seed % 2 == 0) else holdout).append(row)
        if train and holdout:
            return train, holdout, "seed-parity"

    ordered = sorted(rows, key=lambda row: str(row["run_id"]))
    cutoff = int(round(max(1, min(len(rows) - 1, train_fraction * len(rows)))))
    return ordered[:cutoff], ordered[cutoff:], "deterministic-runid-split"


def fit_dominance(rows: List[Dict], coverage_quantile: float) -> Dict[str, float]:
    u_all = [float(r["uncertainty_proxy"]) for r in rows]
    e_all = [float(r["error_proxy"]) for r in rows]
    nominal_errors = [e for u, e in zip(u_all, e_all) if u <= 1e-12]
    c0 = percentile(nominal_errors, 0.95) if nominal_errors else percentile(e_all, 0.05)

    slope_terms = []
    for u, e in zip(u_all, e_all):
        if u <= 1e-12:
            continue
        slope_terms.append(max(0.0, (e - c0) / u))
    c_u = percentile(slope_terms, coverage_quantile) if slope_terms else 0.0

    return {"c_u": c_u, "c_0": c0}


def evaluate_dominance(rows: List[Dict], c_u: float, c_0: float) -> Dict[str, float]:
    if not rows:
        return {
            "empirical_coverage": 0.0,
            "max_violation": 0.0,
            "mae_residual": 0.0,
            "rmse_residual": 0.0,
        }

    hits: List[float] = []
    residuals: List[float] = []
    max_violation = 0.0
    for row in rows:
        u = float(row["uncertainty_proxy"])
        e = float(row["error_proxy"])
        bound = c_u * u + c_0
        residual = e - bound
        residuals.append(residual)
        hits.append(1.0 if residual <= 1e-12 else 0.0)
        max_violation = max(max_violation, residual)

    mae = mean(abs(r) for r in residuals)
    rmse = math.sqrt(mean((r * r) for r in residuals))
    return {
        "empirical_coverage": mean(hits),
        "max_violation": max_violation,
        "mae_residual": mae,
        "rmse_residual": rmse,
    }


def build_bins(rows: List[Dict], n_bins: int = 8) -> List[Dict]:
    us = [float(r["uncertainty_proxy"]) for r in rows]
    es = [float(r["error_proxy"]) for r in rows]
    u_min = min(us)
    u_max = max(us)
    if abs(u_max - u_min) < 1e-12:
        return [{"bin": 1, "u_mean": u_min, "e_mean": mean(es), "count": len(rows)}]

    width = (u_max - u_min) / n_bins
    bins: List[List[Tuple[float, float]]] = [[] for _ in range(n_bins)]
    for u, e in zip(us, es):
        idx = min(n_bins - 1, int((u - u_min) / width))
        bins[idx].append((u, e))

    out: List[Dict] = []
    for idx, bucket in enumerate(bins):
        if not bucket:
            continue
        bu = [x for x, _ in bucket]
        be = [y for _, y in bucket]
        out.append(
            {
                "bin": idx + 1,
                "u_mean": round(mean(bu), 6),
                "e_mean": round(mean(be), 6),
                "count": len(bucket),
            }
        )
    return out


def per_variant(rows: List[Dict]) -> List[Dict]:
    grouped: Dict[str, List[Dict]] = {}
    for row in rows:
        grouped.setdefault(row["variant"], []).append(row)
    out: List[Dict] = []
    for variant in sorted(grouped.keys()):
        g = grouped[variant]
        u = [float(r["uncertainty_proxy"]) for r in g]
        e = [float(r["error_proxy"]) for r in g]
        out.append(
            {
                "variant": variant,
                "n": len(g),
                "u_mean": round(mean(u), 6),
                "e_mean": round(mean(e), 6),
                "u_max": round(max(u), 6),
                "e_max": round(max(e), 6),
            }
        )
    return out


def main() -> int:
    args = parse_args()
    log_dirs = parse_logs_dirs(args.logs_dirs)
    rows = load_rows(log_dirs)

    train_rows, holdout_rows, split_method = split_rows(rows, train_fraction=args.train_fraction)
    fit_train = fit_dominance(train_rows, coverage_quantile=args.coverage_quantile)
    eval_holdout = evaluate_dominance(holdout_rows, fit_train["c_u"], fit_train["c_0"])
    eval_train = evaluate_dominance(train_rows, fit_train["c_u"], fit_train["c_0"])

    u_all = [float(r["uncertainty_proxy"]) for r in rows]
    e_all = [float(r["error_proxy"]) for r in rows]
    slope, intercept, corr = linear_fit(u_all, e_all)
    bins = build_bins(rows, n_bins=8)
    variant_rows = per_variant(rows)

    payload = {
        "source_logs": [str(p) for p in log_dirs],
        "n_rows": len(rows),
        "split": {
            "method": split_method,
            "n_train": len(train_rows),
            "n_holdout": len(holdout_rows),
            "train_fraction": args.train_fraction,
        },
        "assumption_fit": {
            "c_u": round(fit_train["c_u"], 6),
            "c_0": round(fit_train["c_0"], 6),
            "coverage_quantile": args.coverage_quantile,
            "empirical_coverage": round(eval_holdout["empirical_coverage"], 6),
            "max_violation": round(eval_holdout["max_violation"], 6),
        },
        "in_sample_fit": {
            "empirical_coverage": round(eval_train["empirical_coverage"], 6),
            "max_violation": round(eval_train["max_violation"], 6),
        },
        "holdout_metrics": {
            "mae_residual": round(eval_holdout["mae_residual"], 6),
            "rmse_residual": round(eval_holdout["rmse_residual"], 6),
        },
        "linear_relation": {
            "slope": round(slope, 6),
            "intercept": round(intercept, 6),
            "pearson_r": round(corr, 6),
        },
        "binned_scatter": bins,
        "per_variant": variant_rows,
    }

    out_json = pathlib.Path(args.output_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    lines: List[str] = []
    lines.append("# Uncertainty-Dominance Check (Auto-generated)")
    lines.append("")
    lines.append(f"- Source logs: `{', '.join(payload['source_logs'])}`")
    lines.append(f"- Rows analyzed: {payload['n_rows']}")
    lines.append(
        "- Split: "
        f"`{payload['split']['method']}` "
        f"(train={payload['split']['n_train']}, holdout={payload['split']['n_holdout']})"
    )
    lines.append("")
    lines.append("## Fitted Dominance Envelope (Held-out Evaluation)")
    lines.append("")
    lines.append("| c_u | c_0 | Holdout Coverage | Holdout Max Violation | Holdout MAE | Holdout RMSE |")
    lines.append("|---:|---:|---:|---:|---:|---:|")
    lines.append(
        f"| {payload['assumption_fit']['c_u']:.4f} | {payload['assumption_fit']['c_0']:.4f} | "
        f"{payload['assumption_fit']['empirical_coverage']:.3f} | {payload['assumption_fit']['max_violation']:.4f} | "
        f"{payload['holdout_metrics']['mae_residual']:.4f} | {payload['holdout_metrics']['rmse_residual']:.4f} |"
    )
    lines.append("")
    lines.append("## Error-vs-Uncertainty Relationship")
    lines.append("")
    lines.append("| Slope | Intercept | Pearson r |")
    lines.append("|---:|---:|---:|")
    lines.append(
        f"| {payload['linear_relation']['slope']:.4f} | {payload['linear_relation']['intercept']:.4f} | "
        f"{payload['linear_relation']['pearson_r']:.4f} |"
    )
    lines.append("")
    lines.append("## Variant Summary")
    lines.append("")
    lines.append("| Variant | N | Mean U | Mean e | Max U | Max e |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for row in payload["per_variant"]:
        lines.append(
            f"| {row['variant']} | {row['n']} | {row['u_mean']:.4f} | {row['e_mean']:.4f} | "
            f"{row['u_max']:.4f} | {row['e_max']:.4f} |"
        )
    lines.append("")
    lines.append("## Binned Scatter Coordinates (for manuscript figure)")
    lines.append("")
    lines.append("| Bin | Mean U | Mean e | Count |")
    lines.append("|---:|---:|---:|---:|")
    for row in payload["binned_scatter"]:
        lines.append(
            f"| {row['bin']} | {row['u_mean']:.6f} | {row['e_mean']:.6f} | {row['count']} |"
        )

    out_md = pathlib.Path(args.output_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")

    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
