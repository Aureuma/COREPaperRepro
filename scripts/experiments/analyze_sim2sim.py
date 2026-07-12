#!/usr/bin/env python3
"""Analyze sim-to-sim transfer suite outputs and evaluate pass criteria."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
from typing import Dict, List, Tuple


PATTERN = re.compile(r"^SIM-([a-z0-9_]+)-(baseline|ext2|latency_aware|method)-s\d+$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--logs-dir", required=True)
    parser.add_argument("--nominal-summary", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-md", required=True)
    parser.add_argument("--source-engine", default="mujoco")
    parser.add_argument("--max-method-drop-pct", type=float, default=12.0)
    parser.add_argument("--min-gap-retention", type=float, default=0.70)
    return parser.parse_args()


def load_json(path: pathlib.Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def load_runs(path: pathlib.Path) -> List[Dict]:
    rows: List[Dict] = []
    for f in sorted(path.glob("*.json")):
        if f.name == "suite_summary.json":
            continue
        rows.append(json.loads(f.read_text(encoding="utf-8")))
    return rows


def main() -> int:
    args = parse_args()
    runs = load_runs(pathlib.Path(args.logs_dir))
    nominal = load_json(pathlib.Path(args.nominal_summary))

    nominal_method = 0.0
    nominal_baseline = 0.0
    nominal_ext2: float | None = None
    nominal_latency_aware: float | None = None
    nominal_rows = nominal.get("groups", nominal.get("rows", []))
    for row in nominal_rows:
        if row.get("group") == "method":
            nominal_method = float(row.get("mean", 0.0))
        if row.get("group") == "baseline":
            nominal_baseline = float(row.get("mean", 0.0))
        if row.get("group") == "ext2":
            nominal_ext2 = float(row.get("mean", 0.0))
        if row.get("group") == "latency_aware":
            nominal_latency_aware = float(row.get("mean", 0.0))

    grouped: Dict[Tuple[str, str], List[float]] = {}
    for run in runs:
        run_id = str(run.get("run_id", ""))
        match = PATTERN.match(run_id)
        if not match:
            continue
        engine, variant = match.groups()
        value = run.get("metric_payload", {}).get("primary_metric")
        if value is None:
            continue
        grouped.setdefault((engine, variant), []).append(float(value))

    engines = sorted({engine for engine, _ in grouped.keys()})
    rows: List[Dict] = []
    for engine in engines:
        baseline_vals = grouped.get((engine, "baseline"), [])
        ext2_vals = grouped.get((engine, "ext2"), [])
        latency_vals = grouped.get((engine, "latency_aware"), [])
        method_vals = grouped.get((engine, "method"), [])

        baseline = mean(baseline_vals)
        ext2 = mean(ext2_vals)
        latency_aware = mean(latency_vals)
        method = mean(method_vals)
        gap_baseline = method - baseline
        gap_ext2 = method - ext2
        gap_latency = method - latency_aware
        method_drop = (nominal_method - method) / nominal_method * 100.0 if nominal_method > 0 else 0.0
        baseline_drop = (nominal_baseline - baseline) / nominal_baseline * 100.0 if nominal_baseline > 0 else 0.0
        ext2_drop = (
            (nominal_ext2 - ext2) / nominal_ext2 * 100.0
            if nominal_ext2 is not None and nominal_ext2 > 0
            else None
        )
        latency_drop = (
            (nominal_latency_aware - latency_aware) / nominal_latency_aware * 100.0
            if nominal_latency_aware is not None and nominal_latency_aware > 0
            else None
        )
        has_ext2 = len(grouped.get((engine, "ext2"), [])) > 0
        has_latency = len(grouped.get((engine, "latency_aware"), [])) > 0
        rows.append(
            {
                "engine": engine,
                "baseline_n": len(baseline_vals),
                "ext2_n": len(ext2_vals),
                "latency_aware_n": len(latency_vals),
                "method_n": len(method_vals),
                "baseline_mean": baseline,
                "ext2_mean": ext2,
                "latency_aware_mean": latency_aware,
                "method_mean": method,
                "method_minus_baseline": gap_baseline,
                "method_minus_ext2": gap_ext2,
                "method_minus_latency_aware": gap_latency,
                "baseline_drop_pct": baseline_drop,
                "ext2_drop_pct": ext2_drop,
                "latency_aware_drop_pct": latency_drop,
                "method_drop_pct": method_drop,
                "method_beats_baseline": method > baseline,
                "method_beats_ext2": (method > ext2) if has_ext2 else None,
                "method_beats_latency_aware": (method > latency_aware) if has_latency else None,
            }
        )

    by_engine = {row["engine"]: row for row in rows}
    source = by_engine.get(
        args.source_engine,
        {"method_minus_baseline": 0.0, "method_minus_ext2": 0.0, "method_mean": 0.0},
    )
    source_gap_baseline = float(source.get("method_minus_baseline", 0.0))
    source_gap_ext2 = float(source.get("method_minus_ext2", 0.0))
    source_method = float(source.get("method_mean", 0.0))

    criteria: List[Dict] = []
    all_pass = True
    for row in rows:
        c1 = bool(row["method_beats_baseline"])
        c1b_raw = row.get("method_beats_ext2")
        c1b = True if c1b_raw is None else bool(c1b_raw)
        c1c_raw = row.get("method_beats_latency_aware")
        c1c = True if c1c_raw is None else bool(c1c_raw)
        c2 = row["method_drop_pct"] <= args.max_method_drop_pct
        if row["engine"] == args.source_engine:
            c3 = True
            c4 = True
            c5 = True
        else:
            c3 = row["method_minus_baseline"] >= args.min_gap_retention * source_gap_baseline
            if source_gap_ext2 > 0.0 and row.get("method_beats_ext2") is not None:
                c4 = row["method_minus_ext2"] >= args.min_gap_retention * source_gap_ext2
            else:
                c4 = True
            source_gap_latency = float(source.get("method_minus_latency_aware", 0.0))
            if source_gap_latency > 0.0 and row.get("method_beats_latency_aware") is not None:
                c5 = row["method_minus_latency_aware"] >= args.min_gap_retention * source_gap_latency
            else:
                c5 = True

        checks = {
            "method_beats_baseline": c1,
            "method_beats_ext2": c1b,
            "method_beats_latency_aware": c1c,
            "method_drop_within_limit": c2,
            "gap_retention_vs_baseline_ok": c3,
            "gap_retention_vs_ext2_ok": c4,
            "gap_retention_vs_latency_aware_ok": c5,
        }
        passed = all(checks.values())
        all_pass = all_pass and passed
        criteria.append(
            {
                "engine": row["engine"],
                "checks": checks,
                "pass": passed,
            }
        )

    out = {
        "nominal_baseline": nominal_baseline,
        "nominal_ext2": nominal_ext2,
        "nominal_latency_aware": nominal_latency_aware,
        "nominal_method": nominal_method,
        "source_engine": args.source_engine,
        "source_method_mean": source_method,
        "source_gap_baseline": source_gap_baseline,
        "source_gap_ext2": source_gap_ext2,
        "rows": rows,
        "criteria": criteria,
        "all_required_pass": all_pass,
        "thresholds": {
            "max_method_drop_pct": args.max_method_drop_pct,
            "min_gap_retention": args.min_gap_retention,
        },
    }

    out_json = pathlib.Path(args.output_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")

    lines: List[str] = []
    lines.append("# Sim-to-Sim Transfer Results (Auto-generated)")
    lines.append("")
    lines.append(f"- Source logs: `{args.logs_dir}`")
    lines.append(f"- Nominal baseline mean: {nominal_baseline:.4f}")
    lines.append(f"- Nominal ext2 mean: {f'{nominal_ext2:.4f}' if nominal_ext2 is not None else 'N/A'}")
    lines.append(
        f"- Nominal latency_aware mean: {f'{nominal_latency_aware:.4f}' if nominal_latency_aware is not None else 'N/A'}"
    )
    lines.append(f"- Nominal method mean: {nominal_method:.4f}")
    lines.append(f"- Source engine: `{args.source_engine}`")
    lines.append(f"- Thresholds: method drop <= {args.max_method_drop_pct:.1f}%, gap retention >= {args.min_gap_retention:.2f}")
    lines.append("")
    lines.append(
        "| Engine | N | Baseline Mean | ext2 Mean | latency_aware Mean | Method Mean | Method-Baseline | Method-ext2 | Method-latency_aware | Baseline Drop % | ext2 Drop % | latency_aware Drop % | Method Drop % | Method > Baseline | Method > ext2 | Method > latency_aware |"
    )
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|")
    for row in rows:
        beats_ext2 = row["method_beats_ext2"]
        beats_ext2_text = "N/A" if beats_ext2 is None else ("YES" if beats_ext2 else "NO")
        beats_latency = row["method_beats_latency_aware"]
        beats_latency_text = "N/A" if beats_latency is None else ("YES" if beats_latency else "NO")
        ext2_drop_text = "N/A" if row["ext2_drop_pct"] is None else f"{row['ext2_drop_pct']:.2f}%"
        latency_drop_text = "N/A" if row["latency_aware_drop_pct"] is None else f"{row['latency_aware_drop_pct']:.2f}%"
        lines.append(
            f"| {row['engine']} | {row['method_n']} | {row['baseline_mean']:.4f} | {row['ext2_mean']:.4f} | {row['latency_aware_mean']:.4f} | {row['method_mean']:.4f} | "
            f"{row['method_minus_baseline']:+.4f} | {row['method_minus_ext2']:+.4f} | {row['method_minus_latency_aware']:+.4f} | "
            f"{row['baseline_drop_pct']:.2f}% | {ext2_drop_text} | {latency_drop_text} | {row['method_drop_pct']:.2f}% | "
            f"{'YES' if row['method_beats_baseline'] else 'NO'} | {beats_ext2_text} | {beats_latency_text} |"
        )
    if not rows:
        lines.append("| _none_ | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0% | 0% | 0% | 0% | NO | NO | NO |")

    lines.append("")
    lines.append("| Engine | Method>Baseline | Method>ext2 | Method>latency_aware | Drop<=Limit | GapRet(base) | GapRet(ext2) | GapRet(latency_aware) | Status |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for row in criteria:
        checks = row["checks"]
        lines.append(
            f"| {row['engine']} | {'PASS' if checks['method_beats_baseline'] else 'FAIL'} | "
            f"{'PASS' if checks['method_beats_ext2'] else 'FAIL'} | "
            f"{'PASS' if checks['method_beats_latency_aware'] else 'FAIL'} | "
            f"{'PASS' if checks['method_drop_within_limit'] else 'FAIL'} | "
            f"{'PASS' if checks['gap_retention_vs_baseline_ok'] else 'FAIL'} | "
            f"{'PASS' if checks['gap_retention_vs_ext2_ok'] else 'FAIL'} | "
            f"{'PASS' if checks['gap_retention_vs_latency_aware_ok'] else 'FAIL'} | "
            f"{'PASS' if row['pass'] else 'FAIL'} |"
        )
    lines.append("")
    lines.append(f"- Required sim-to-sim criteria pass: {'YES' if all_pass else 'NO'}")

    out_md = pathlib.Path(args.output_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
