#!/usr/bin/env python3
"""Analyze software-transfer suite outputs and evaluate pass criteria."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
from typing import Dict, List, Tuple


PATTERN = re.compile(r"^(S\d+)-([a-z]+)-(baseline|method)-s\d+$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--logs-dir", required=True)
    parser.add_argument("--nominal-summary", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-md", required=True)
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


def status_for(test: str, severity: str, baseline: float, method: float, nominal_method: float) -> Tuple[str, str]:
    # Returns (pass_fail, criterion_text)
    if test == "S1" and severity == "hard":
        return (
            "PASS" if method > baseline else "FAIL",
            "method > baseline under hard long-horizon shift",
        )
    if test == "S2" and severity == "med":
        drop = (nominal_method - method) / nominal_method * 100.0
        return ("PASS" if drop <= 12.0 else "FAIL", "method drop <= 12% at med temporal jitter")
    if test == "S3" and severity == "severe":
        drop = (nominal_method - method) / nominal_method * 100.0
        ok = drop <= 18.0 and method > baseline
        return (
            "PASS" if ok else "FAIL",
            "method > baseline and drop <= 18% under severe observation dropout",
        )
    return ("N/A", "informational")


def main() -> int:
    args = parse_args()
    runs = load_runs(pathlib.Path(args.logs_dir))
    nominal = load_json(pathlib.Path(args.nominal_summary))
    nominal_method = 0.0
    nominal_baseline = 0.0
    for row in nominal.get("groups", []):
        if row.get("group") == "method":
            nominal_method = float(row.get("mean", 0.0))
        if row.get("group") == "baseline":
            nominal_baseline = float(row.get("mean", 0.0))

    grouped: Dict[Tuple[str, str, str], List[float]] = {}
    for run in runs:
        run_id = str(run.get("run_id", ""))
        match = PATTERN.match(run_id)
        if not match:
            continue
        test, severity, variant = match.groups()
        value = run.get("metric_payload", {}).get("primary_metric")
        if value is None:
            continue
        grouped.setdefault((test, severity, variant), []).append(float(value))

    rows = []
    tests = sorted({key[0] for key in grouped.keys()})
    for test in tests:
        severities = sorted({key[1] for key in grouped.keys() if key[0] == test})
        for severity in severities:
            baseline = mean(grouped.get((test, severity, "baseline"), []))
            method = mean(grouped.get((test, severity, "method"), []))
            pass_fail, criterion = status_for(test, severity, baseline, method, nominal_method)
            method_drop = (nominal_method - method) / nominal_method * 100.0 if nominal_method > 0 else 0.0
            baseline_drop = (nominal_baseline - baseline) / nominal_baseline * 100.0 if nominal_baseline > 0 else 0.0
            rows.append(
                {
                    "test": test,
                    "severity": severity,
                    "baseline_mean": baseline,
                    "method_mean": method,
                    "baseline_drop_pct": baseline_drop,
                    "method_drop_pct": method_drop,
                    "criterion": criterion,
                    "status": pass_fail,
                }
            )

    out = {
        "nominal_baseline": nominal_baseline,
        "nominal_method": nominal_method,
        "rows": rows,
        "all_required_pass": all(r["status"] in {"PASS", "N/A"} for r in rows),
    }
    out_json = pathlib.Path(args.output_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")

    lines: List[str] = []
    lines.append("# Software Transfer Results (Auto-generated)")
    lines.append("")
    lines.append(f"- Source: `{args.logs_dir}`")
    lines.append(f"- Nominal baseline mean: {nominal_baseline:.4f}")
    lines.append(f"- Nominal method mean: {nominal_method:.4f}")
    lines.append("")
    lines.append("| Test | Severity | Baseline Mean | Method Mean | Baseline Drop % | Method Drop % | Criterion | Status |")
    lines.append("|---|---|---:|---:|---:|---:|---|---|")
    for row in rows:
        lines.append(
            f"| {row['test']} | {row['severity']} | {row['baseline_mean']:.4f} | {row['method_mean']:.4f} | "
            f"{row['baseline_drop_pct']:.2f}% | {row['method_drop_pct']:.2f}% | {row['criterion']} | {row['status']} |"
        )
    if not rows:
        lines.append("| _none_ |  | 0 | 0 | 0% | 0% |  |  |")

    lines.append("")
    lines.append(f"- Required software-transfer criteria pass: {'YES' if out['all_required_pass'] else 'NO'}")
    out_md = pathlib.Path(args.output_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
