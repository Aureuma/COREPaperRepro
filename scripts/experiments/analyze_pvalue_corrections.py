#!/usr/bin/env python3
"""Apply multiple-comparison corrections to pairwise p-values."""

from __future__ import annotations

import argparse
import json
import pathlib
from typing import Dict, List, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-json", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-md", required=True)
    parser.add_argument("--family-name", default="comparison-family")
    parser.add_argument("--rows-key", default="auto")
    parser.add_argument("--alpha", type=float, default=0.05)
    return parser.parse_args()


def load_rows(payload: Dict, rows_key: str) -> List[Dict]:
    if rows_key != "auto":
        rows = payload.get(rows_key, [])
        return rows if isinstance(rows, list) else []
    for key in ("comparisons", "rows"):
        rows = payload.get(key, [])
        if isinstance(rows, list) and rows:
            return rows
    return []


def bonferroni(p: List[float]) -> List[float]:
    m = len(p)
    return [min(1.0, x * m) for x in p]


def holm_bonferroni(p: List[float]) -> List[float]:
    m = len(p)
    order = sorted(range(m), key=lambda i: p[i])
    out = [1.0] * m
    prev = 0.0
    for rank, idx in enumerate(order):
        value = max(prev, (m - rank) * p[idx])
        prev = value
        out[idx] = min(1.0, value)
    return out


def benjamini_hochberg(p: List[float]) -> List[float]:
    m = len(p)
    order_desc = sorted(range(m), key=lambda i: p[i], reverse=True)
    out = [1.0] * m
    prev = 1.0
    for rev_rank, idx in enumerate(order_desc, start=1):
        rank = m - rev_rank + 1
        value = min(prev, p[idx] * m / rank)
        prev = value
        out[idx] = min(1.0, value)
    return out


def row_name(row: Dict, i: int) -> str:
    if "reference_group" in row and "comparator_group" in row:
        return f"{row['reference_group']} vs {row['comparator_group']}"
    if "group" in row:
        return str(row["group"])
    return f"row_{i+1}"


def ci_bounds(row: Dict) -> Tuple[float | None, float | None]:
    delta = row.get("delta_mean")
    half = row.get("delta_ci95_halfwidth")
    if delta is None or half is None:
        return None, None
    d = float(delta)
    h = float(half)
    return d - h, d + h


def main() -> int:
    args = parse_args()
    payload = json.loads(pathlib.Path(args.input_json).read_text(encoding="utf-8"))
    rows = load_rows(payload, args.rows_key)
    if not rows:
        raise SystemExit(f"No comparison rows found in {args.input_json}")

    pvals = [float(row.get("p_two_sided", 1.0)) for row in rows]
    bonf = bonferroni(pvals)
    holm = holm_bonferroni(pvals)
    bh = benjamini_hochberg(pvals)

    out_rows: List[Dict] = []
    for i, row in enumerate(rows):
        lo, hi = ci_bounds(row)
        out_rows.append(
            {
                "comparison": row_name(row, i),
                "p_raw": pvals[i],
                "p_bonferroni": bonf[i],
                "p_holm": holm[i],
                "q_bh": bh[i],
                "significant_raw_alpha": pvals[i] < args.alpha,
                "significant_holm_alpha": holm[i] < args.alpha,
                "significant_bh_alpha": bh[i] < args.alpha,
                "delta_mean": row.get("delta_mean"),
                "delta_ci95_halfwidth": row.get("delta_ci95_halfwidth"),
                "delta_ci95_lower": lo,
                "delta_ci95_upper": hi,
                "ci95_excludes_zero": (lo is not None and hi is not None and (lo > 0.0 or hi < 0.0)),
                "cohen_d": row.get("cohen_d"),
            }
        )

    summary = {
        "family_name": args.family_name,
        "alpha": args.alpha,
        "input_json": args.input_json,
        "num_tests": len(rows),
        "holm_significant_count": sum(1 for r in out_rows if r["significant_holm_alpha"]),
        "bh_significant_count": sum(1 for r in out_rows if r["significant_bh_alpha"]),
    }
    out_payload = {"summary": summary, "rows": out_rows}

    out_json = pathlib.Path(args.output_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(out_payload, indent=2) + "\n", encoding="utf-8")

    lines: List[str] = []
    lines.append(f"# P-value Corrections ({args.family_name})")
    lines.append("")
    lines.append(f"- Input: `{args.input_json}`")
    lines.append(f"- Tests in family: `{len(rows)}`")
    lines.append(f"- Alpha: `{args.alpha:.2f}`")
    lines.append("")
    lines.append("| Comparison | p(raw) | p(Holm) | q(BH) | Sig(Holm) | Delta Mean | CI95 Excludes 0 | Cohen's d |")
    lines.append("|---|---:|---:|---:|---|---:|---|---:|")
    for row in out_rows:
        d = row["delta_mean"]
        d_txt = f"{float(d):+.4f}" if d is not None else "n/a"
        cd = row["cohen_d"]
        cd_txt = f"{float(cd):.3f}" if cd is not None else "n/a"
        lines.append(
            f"| {row['comparison']} | {row['p_raw']:.6f} | {row['p_holm']:.6f} | {row['q_bh']:.6f} | "
            f"{'YES' if row['significant_holm_alpha'] else 'NO'} | {d_txt} | "
            f"{'YES' if row['ci95_excludes_zero'] else 'NO'} | {cd_txt} |"
        )

    lines.append("")
    lines.append(f"- Holm-significant comparisons: `{summary['holm_significant_count']}/{len(rows)}`")
    lines.append(f"- BH-significant comparisons: `{summary['bh_significant_count']}/{len(rows)}`")

    out_md = pathlib.Path(args.output_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
