#!/usr/bin/env python3
"""Quantify gate-envelope decision robustness under (c_u, c_0) misspecification."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
from typing import Any


DEFAULT_LOG_DIRS = ",".join(
    [
        "output/corepaper_logs/experiments/external_latest",
        "output/corepaper_logs/experiments/robustness_latest",
        "output/corepaper_logs/experiments/software_transfer_latest",
        "output/corepaper_logs/experiments/sim2sim_latest",
        "output/corepaper_logs/experiments/recent_baselines_latest",
    ]
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--logs-dirs", default=DEFAULT_LOG_DIRS)
    parser.add_argument(
        "--uncertainty-json",
        default="output/corepaper_reports/ws5/uncertainty_dominance.json",
    )
    parser.add_argument("--cu-scale-list", default="0.8,0.9,1.0,1.1,1.2")
    parser.add_argument("--c0-shift-list", default="-0.01,-0.005,0.0,0.005,0.01")
    parser.add_argument(
        "--output-json",
        default="output/corepaper_reports/ws5/uncertainty_misspec_sensitivity.json",
    )
    parser.add_argument(
        "--output-md",
        default="output/corepaper_reports/ws5/uncertainty_misspec_sensitivity.md",
    )
    return parser.parse_args()


def parse_logs_dirs(raw: str) -> list[pathlib.Path]:
    dirs = [pathlib.Path(item.strip()) for item in raw.split(",") if item.strip()]
    if not dirs:
        raise ValueError("No log directories specified.")
    return dirs


def parse_float_list(raw: str) -> list[float]:
    out: list[float] = []
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        out.append(float(token))
    if not out:
        raise ValueError("Expected at least one numeric value.")
    return out


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


def load_rows(log_dirs: list[pathlib.Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
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
            base = float(comp["base_score"])
            u = abs(float(comp["total_penalty"]))
            e = abs(base - float(observed))
            rows.append(
                {
                    "run_id": run_id,
                    "seed": extract_seed(run_id),
                    "variant": str(payload.get("resolved_variant") or payload.get("variant") or "unknown"),
                    "scenario": str(payload.get("scenario") or "unknown"),
                    "uncertainty_proxy": u,
                    "error_proxy": e,
                }
            )
    if not rows:
        raise ValueError("No compatible rows found in provided logs.")
    return rows


def split_rows_seed_parity(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str]:
    with_seed = [row for row in rows if isinstance(row.get("seed"), int)]
    if len(with_seed) >= max(10, len(rows) // 3):
        train: list[dict[str, Any]] = []
        holdout: list[dict[str, Any]] = []
        for row in rows:
            seed = row.get("seed")
            if not isinstance(seed, int):
                bucket = stable_hash(str(row["run_id"])) % 2
                (train if bucket == 0 else holdout).append(row)
                continue
            (train if (seed % 2 == 0) else holdout).append(row)
        if train and holdout:
            return train, holdout, "seed-parity"
    ordered = sorted(rows, key=lambda row: str(row.get("run_id", "")))
    cut = max(1, min(len(ordered) - 1, int(round(0.8 * len(ordered)))))
    return ordered[:cut], ordered[cut:], "deterministic-runid-split"


def evaluate_decisions(
    rows: list[dict[str, Any]],
    *,
    c_u: float,
    c_0: float,
    base_accept: list[bool],
) -> dict[str, Any]:
    n = len(rows)
    accepts: list[bool] = []
    max_violation = 0.0
    mean_margin = 0.0
    false_accept = 0
    false_reject = 0
    agreement = 0

    for idx, row in enumerate(rows):
        u = float(row["uncertainty_proxy"])
        e = float(row["error_proxy"])
        residual = e - (c_u * u + c_0)
        accept = residual <= 0.0
        accepts.append(accept)
        if residual > max_violation:
            max_violation = residual
        mean_margin += -residual
        if accept == base_accept[idx]:
            agreement += 1
        elif accept and not base_accept[idx]:
            false_accept += 1
        elif (not accept) and base_accept[idx]:
            false_reject += 1

    return {
        "n_rows": n,
        "accept_rate": (sum(1 for x in accepts if x) / n) if n else 0.0,
        "decision_agreement_vs_base": (agreement / n) if n else 0.0,
        "false_accept_vs_base_rate": (false_accept / n) if n else 0.0,
        "false_reject_vs_base_rate": (false_reject / n) if n else 0.0,
        "max_violation": max_violation,
        "mean_margin": (mean_margin / n) if n else 0.0,
    }


def markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Gate-Envelope Misspecification Sensitivity (Auto-generated)")
    lines.append("")
    lines.append(
        f"- Base constants: c_u={payload['base_fit']['c_u']:.4f}, c_0={payload['base_fit']['c_0']:.4f}"
    )
    lines.append(
        f"- Holdout rows: {payload['holdout_rows']} (split={payload['split_method']})"
    )
    lines.append(
        f"- Base accept rate: {payload['base_fit']['accept_rate']:.3f}; "
        f"worst agreement in sweep: {payload['summary']['worst_agreement']:.3f}"
    )
    lines.append("")
    lines.append(
        "| c_u scale | c_0 shift | c_u | c_0 | Agree vs base | False accept | False reject | Accept rate | Max violation | Mean margin |"
    )
    lines.append("|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for row in payload["rows"]:
        lines.append(
            f"| {row['cu_scale']:.3f} | {row['c0_shift']:+.4f} | {row['c_u']:.4f} | {row['c_0']:.4f} | "
            f"{row['decision_agreement_vs_base']:.3f} | {row['false_accept_vs_base_rate']:.3f} | "
            f"{row['false_reject_vs_base_rate']:.3f} | {row['accept_rate']:.3f} | {row['max_violation']:.4f} | {row['mean_margin']:.4f} |"
        )
    return "\n".join(lines).strip() + "\n"


def main() -> int:
    args = parse_args()
    log_dirs = parse_logs_dirs(args.logs_dirs)
    rows = load_rows(log_dirs)
    _, holdout_rows, split_method = split_rows_seed_parity(rows)

    uncertainty_path = pathlib.Path(args.uncertainty_json)
    uncertainty = json.loads(uncertainty_path.read_text(encoding="utf-8"))
    base_fit = uncertainty.get("assumption_fit", {})
    base_cu = float(base_fit.get("c_u", 0.0))
    base_c0 = float(base_fit.get("c_0", 0.0))

    base_accept = [
        float(row["error_proxy"]) - (base_cu * float(row["uncertainty_proxy"]) + base_c0) <= 0.0
        for row in holdout_rows
    ]
    base_accept_rate = (sum(1 for x in base_accept if x) / len(base_accept)) if base_accept else 0.0

    cu_scales = parse_float_list(args.cu_scale_list)
    c0_shifts = parse_float_list(args.c0_shift_list)
    rows_out: list[dict[str, Any]] = []
    for cu_scale in cu_scales:
        for c0_shift in c0_shifts:
            c_u = base_cu * cu_scale
            c_0 = base_c0 + c0_shift
            eval_row = evaluate_decisions(
                holdout_rows,
                c_u=c_u,
                c_0=c_0,
                base_accept=base_accept,
            )
            rows_out.append(
                {
                    "cu_scale": round(cu_scale, 6),
                    "c0_shift": round(c0_shift, 6),
                    "c_u": round(c_u, 6),
                    "c_0": round(c_0, 6),
                    **{k: round(float(v), 6) for k, v in eval_row.items() if k != "n_rows"},
                    "n_rows": eval_row["n_rows"],
                }
            )
    rows_out.sort(key=lambda row: (row["cu_scale"], row["c0_shift"]))

    worst_agreement = min((float(row["decision_agreement_vs_base"]) for row in rows_out), default=0.0)
    max_false_accept = max((float(row["false_accept_vs_base_rate"]) for row in rows_out), default=0.0)
    max_false_reject = max((float(row["false_reject_vs_base_rate"]) for row in rows_out), default=0.0)

    payload = {
        "source_logs": [str(p) for p in log_dirs],
        "source_uncertainty_json": str(uncertainty_path),
        "split_method": split_method,
        "holdout_rows": len(holdout_rows),
        "base_fit": {
            "c_u": round(base_cu, 6),
            "c_0": round(base_c0, 6),
            "accept_rate": round(base_accept_rate, 6),
        },
        "grid": {
            "cu_scales": [round(x, 6) for x in cu_scales],
            "c0_shifts": [round(x, 6) for x in c0_shifts],
            "n_rows": len(rows_out),
        },
        "summary": {
            "worst_agreement": round(worst_agreement, 6),
            "max_false_accept_rate": round(max_false_accept, 6),
            "max_false_reject_rate": round(max_false_reject, 6),
        },
        "rows": rows_out,
    }

    out_json = pathlib.Path(args.output_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    out_md = pathlib.Path(args.output_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(markdown(payload), encoding="utf-8")

    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
