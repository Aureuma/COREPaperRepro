#!/usr/bin/env python3
"""Analyze baseline calibration against predefined target profiles."""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Dict, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary-json", required=True, help="Path to external baseline summary JSON.")
    parser.add_argument("--targets-json", required=True, help="Path to calibration target JSON.")
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-md", required=True)
    return parser.parse_args()


def load_json(path: pathlib.Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    args = parse_args()
    summary = load_json(pathlib.Path(args.summary_json))
    targets = load_json(pathlib.Path(args.targets_json))

    observed = {row.get("group"): float(row.get("mean", 0.0)) for row in summary.get("rows", [])}
    default_tol = float(targets.get("default_tolerance_abs", 0.005))

    rows: List[Dict] = []
    for target in targets.get("targets", []):
        group = str(target["group"])
        target_mean = float(target["target_mean"])
        tol = float(target.get("tolerance_abs", default_tol))
        obs = observed.get(group)
        if obs is None:
            rows.append(
                {
                    "group": group,
                    "target_mean": target_mean,
                    "observed_mean": None,
                    "abs_error": None,
                    "tolerance_abs": tol,
                    "status": "MISSING",
                    "source": target.get("source", ""),
                }
            )
            continue
        abs_error = abs(obs - target_mean)
        rows.append(
            {
                "group": group,
                "target_mean": target_mean,
                "observed_mean": obs,
                "abs_error": abs_error,
                "tolerance_abs": tol,
                "status": "PASS" if abs_error <= tol else "FAIL",
                "source": target.get("source", ""),
            }
        )

    all_pass = all(row["status"] == "PASS" for row in rows)
    out = {
        "summary_json": args.summary_json,
        "targets_json": args.targets_json,
        "rows": rows,
        "all_required_pass": all_pass,
    }

    out_json = pathlib.Path(args.output_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")

    lines: List[str] = []
    lines.append("# Baseline Calibration Report (Auto-generated)")
    lines.append("")
    lines.append(f"- Source summary: `{args.summary_json}`")
    lines.append(f"- Targets: `{args.targets_json}`")
    lines.append("")
    lines.append("| Group | Target Mean | Observed Mean | Abs Error | Tolerance | Status | Source |")
    lines.append("|---|---:|---:|---:|---:|---|---|")
    for row in rows:
        obs = "-" if row["observed_mean"] is None else f"{row['observed_mean']:.4f}"
        err = "-" if row["abs_error"] is None else f"{row['abs_error']:.4f}"
        lines.append(
            f"| {row['group']} | {row['target_mean']:.4f} | {obs} | {err} | "
            f"{row['tolerance_abs']:.4f} | {row['status']} | {row['source']} |"
        )
    if not rows:
        lines.append("| _none_ | 0 | 0 | 0 | 0 | FAIL | n/a |")
    lines.append("")
    lines.append(f"- Calibration pass: {'YES' if all_pass else 'NO'}")

    out_md = pathlib.Path(args.output_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
