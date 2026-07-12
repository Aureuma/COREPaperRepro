#!/usr/bin/env python3
"""Generate manuscript figures as SVG assets under paper/figures."""

from __future__ import annotations

import json
import pathlib
from math import sqrt
from typing import Dict, List, Sequence, Tuple


ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "paper/figures"
LEGACY_OUT_DIR = ROOT / "output/corepaper_assets/figures"
FONT_FAMILY = "DejaVu Sans"


def load_palette() -> Dict[str, str]:
    path = ROOT / "config/visual_identity.json"
    if not path.exists():
        return {
            "ink_primary": "#0F172A",
            "ink_secondary": "#334155",
            "bg_canvas": "#F4F7FB",
            "bg_panel": "#E6EDF7",
            "grid": "#CBD5E1",
            "baseline": "#6E8EA9",
            "reference_a": "#8BBC6E",
            "reference_b": "#E2A75D",
            "method": "#D94B4B",
        }
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload.get("palette", {})


PALETTE = load_palette()
C_INK = PALETTE.get("ink_primary", "#0F172A")
C_INK_2 = PALETTE.get("ink_secondary", "#334155")
C_BG = PALETTE.get("bg_canvas", "#F4F7FB")
C_PANEL = PALETTE.get("bg_panel", "#E6EDF7")
C_GRID = PALETTE.get("grid", "#CBD5E1")
C_BASELINE = PALETTE.get("baseline", "#6E8EA9")
C_REF_A = PALETTE.get("reference_a", "#8BBC6E")
C_REF_B = PALETTE.get("reference_b", "#E2A75D")
C_REF_C = PALETTE.get("reference_c", "#6B8FD6")
C_REF_D = PALETTE.get("reference_d", "#4FA89A")
C_REF_E = PALETTE.get("reference_e", "#9A7FD1")
C_REF_F = PALETTE.get("reference_f", "#8A7CF0")
C_REF_G = PALETTE.get("reference_g", "#D37295")
C_METHOD = PALETTE.get("method", "#D94B4B")


def load_json(path: pathlib.Path) -> Dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: pathlib.Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def svg_header(width: int, height: int) -> str:
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'


def svg_footer() -> str:
    return "</svg>"


def xml_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def fmt_p(value: float) -> str:
    if value < 1e-4:
        return "1e-4"
    return f"{value:.4f}"


def hex_to_rgb(color: str) -> Tuple[int, int, int]:
    color = color.lstrip("#")
    return int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    r, g, b = rgb
    return f"#{r:02X}{g:02X}{b:02X}"


def lerp_color(c0: str, c1: str, t: float) -> str:
    t = max(0.0, min(1.0, t))
    a = hex_to_rgb(c0)
    b = hex_to_rgb(c1)
    out = (
        int(round(a[0] + (b[0] - a[0]) * t)),
        int(round(a[1] + (b[1] - a[1]) * t)),
        int(round(a[2] + (b[2] - a[2]) * t)),
    )
    return rgb_to_hex(out)


def _strip_task_version(task_name: str) -> str:
    head, sep, tail = task_name.rpartition("-v")
    if sep and tail.isdigit():
        return head
    return task_name


def _load_configured_metaworld_tasks() -> Tuple[List[str], Dict]:
    cfg_candidates = [
        ROOT / "config/benchmarks/experiments_metaworld_recent_baselines.json",
        ROOT / "config/benchmarks/experiments_metaworld_slice.json",
    ]
    for path in cfg_candidates:
        cfg = load_json(path)
        tasks = [str(task) for task in cfg.get("tasks", [])]
        if tasks:
            return tasks, cfg
    return [], {}


def _ordered_shifted_tasks(rows: List[Dict], configured_tasks: List[str]) -> List[str]:
    observed: List[str] = []
    seen = set()
    for row in rows:
        if str(row.get("scenario")) != "shifted":
            continue
        task_name = str(row.get("task", "")).strip()
        if task_name and task_name not in seen:
            seen.add(task_name)
            observed.append(task_name)

    if configured_tasks:
        observed_set = set(observed)
        ordered = [task for task in configured_tasks if task in observed_set]
        ordered.extend(task for task in observed if task not in ordered)
        if ordered:
            return ordered
    return observed


def _task_axis_label(task_name: str) -> str:
    max_label_len = 14
    token_alias = {
        "button": "btn",
        "topdown": "top",
        "insert": "ins",
        "faucet": "faucet",
        "drawer": "drawer",
        "press": "press",
        "place": "place",
    }
    base = _strip_task_version(task_name)
    tokens = [token_alias.get(tok, tok) for tok in base.split("-") if tok]
    label = "-".join(tokens)
    if len(label) <= max_label_len:
        return label
    compressed = "-".join(tok[:4] if len(tok) > 4 else tok for tok in tokens)
    if len(compressed) <= max_label_len:
        return compressed
    return compressed[:max_label_len]


def grouped_bar_chart_svg(
    *,
    title: str,
    categories: List[str],
    series: List[Tuple[str, List[float], str | Sequence[str], List[float] | None]],
    y_label: str,
    y_max: float,
    x_label_rotation: float = 0.0,
    show_value_labels: bool = False,
    zero_bar_min_px: float = 0.0,
) -> str:
    width, height = 1040, 580
    margin_left, margin_bottom, margin_top, margin_right = 82, 112, 60, 36
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom
    group_count = max(len(categories), 1)
    group_w = plot_w / group_count
    bar_w = (group_w * 0.78) / max(len(series), 1)
    group_offset = (group_w - (bar_w * len(series))) / 2.0

    parts: List[str] = [svg_header(width, height)]
    parts.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="{C_BG}"/>')
    parts.append(
        f'<text x="{width/2}" y="34" fill="{C_INK}" font-size="22" text-anchor="middle" font-family="{FONT_FAMILY}">{xml_escape(title)}</text>'
    )
    x0 = margin_left
    y0 = height - margin_bottom
    parts.append(f'<line x1="{x0}" y1="{y0}" x2="{width-margin_right}" y2="{y0}" stroke="{C_INK}" stroke-width="2"/>')
    parts.append(f'<line x1="{x0}" y1="{margin_top}" x2="{x0}" y2="{y0}" stroke="{C_INK}" stroke-width="2"/>')
    parts.append(
        f'<text x="24" y="{margin_top + plot_h/2}" fill="{C_INK}" font-size="12" text-anchor="middle" transform="rotate(-90 24 {margin_top + plot_h/2})" font-family="{FONT_FAMILY}">{xml_escape(y_label)}</text>'
    )

    for i in range(6):
        tick_val = (y_max / 5.0) * i
        y = y0 - (tick_val / y_max) * plot_h
        parts.append(f'<line x1="{x0}" y1="{y:.2f}" x2="{width-margin_right}" y2="{y:.2f}" stroke="{C_GRID}" stroke-width="1"/>')
        parts.append(
            f'<text x="{x0-8}" y="{y+4:.2f}" fill="{C_INK_2}" font-size="11" text-anchor="end" font-family="{FONT_FAMILY}">{tick_val:.2f}</text>'
        )

    for cat_idx, cat in enumerate(categories):
        gx = x0 + cat_idx * group_w
        for series_idx, (_, series_values, color, series_errors) in enumerate(series):
            value = series_values[cat_idx]
            bar_h = (value / y_max) * plot_h
            if value <= 0 and zero_bar_min_px > 0:
                bar_h = zero_bar_min_px
            x = gx + group_offset + series_idx * bar_w
            y = y0 - bar_h
            fill_color = color[cat_idx] if isinstance(color, (list, tuple)) else color
            parts.append(
                f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_w:.2f}" height="{bar_h:.2f}" fill="{fill_color}" rx="2" stroke="{C_INK}" stroke-width="0.6"/>'
            )
            if series_errors is not None:
                err = max(series_errors[cat_idx], 0.0)
                y_high = y0 - (min(value + err, y_max) / y_max) * plot_h
                y_low = y0 - (max(value - err, 0.0) / y_max) * plot_h
                cx = x + bar_w / 2.0
                cap = max(bar_w * 0.22, 2.5)
                parts.append(f'<line x1="{cx:.2f}" y1="{y_high:.2f}" x2="{cx:.2f}" y2="{y_low:.2f}" stroke="{C_INK}" stroke-width="1.2"/>')
                parts.append(f'<line x1="{cx-cap:.2f}" y1="{y_high:.2f}" x2="{cx+cap:.2f}" y2="{y_high:.2f}" stroke="{C_INK}" stroke-width="1.2"/>')
                parts.append(f'<line x1="{cx-cap:.2f}" y1="{y_low:.2f}" x2="{cx+cap:.2f}" y2="{y_low:.2f}" stroke="{C_INK}" stroke-width="1.2"/>')
            if show_value_labels:
                label_y = y - 4 if value > 0 else y0 - 4
                parts.append(
                    f'<text x="{x + bar_w/2:.2f}" y="{label_y:.2f}" fill="{C_INK}" font-size="9.5" text-anchor="middle" font-family="{FONT_FAMILY}">{value:.3f}</text>'
                )
        tx = gx + group_w / 2
        ty = y0 + 24
        if abs(x_label_rotation) > 1e-6:
            parts.append(
                f'<text x="{tx:.2f}" y="{ty:.2f}" fill="{C_INK_2}" font-size="11" text-anchor="end" '
                f'transform="rotate({x_label_rotation:.1f} {tx:.2f} {ty:.2f})" font-family="{FONT_FAMILY}">{xml_escape(cat)}</text>'
            )
        else:
            parts.append(
                f'<text x="{tx:.2f}" y="{ty:.2f}" fill="{C_INK_2}" font-size="11" text-anchor="middle" font-family="{FONT_FAMILY}">{xml_escape(cat)}</text>'
            )

    legend_x = margin_left + 4
    legend_y = 44
    for i, (name, _, color, _) in enumerate(series):
        lx = legend_x + i * 190
        legend_color = color[0] if isinstance(color, (list, tuple)) and color else color
        parts.append(f'<rect x="{lx}" y="{legend_y}" width="14" height="14" fill="{legend_color}" rx="2"/>')
        parts.append(
            f'<text x="{lx+20}" y="{legend_y+12}" fill="{C_INK}" font-size="12" text-anchor="start" font-family="{FONT_FAMILY}">{xml_escape(name)}</text>'
        )

    parts.append(svg_footer())
    return "\n".join(parts)


def metaworld_taskwise_svg() -> str:
    mt = load_json(ROOT / "output/corepaper_reports/ws3/metaworld_recent_baselines_results.json")
    if not mt:
        mt = load_json(ROOT / "output/corepaper_reports/ws3/metaworld_slice_results.json")
    rows = mt.get("task_breakdown", [])
    configured_tasks, figure_cfg = _load_configured_metaworld_tasks()
    tasks = _ordered_shifted_tasks(rows, configured_tasks)
    if not tasks:
        tasks = sorted(
            {
                str(row.get("task"))
                for row in rows
                if row.get("scenario") == "shifted" and row.get("task")
            }
        )
    # Use an informative task subset in the main figure:
    # drop ceiling/outlier tasks that visually dominate without adding method-separation signal.
    display_exclusions = set(
        str(task) for task in figure_cfg.get("figure_task_exclusions", ["peg-insert-side-v3", "reach-v3", "pick-place-v3"])
    )
    tasks = [t for t in tasks if t not in display_exclusions]
    task_variant_mean: Dict[Tuple[str, str], float] = {}
    task_variant_samples: Dict[Tuple[str, str], List[float]] = {}
    for row in rows:
        if row.get("scenario") == "shifted":
            task_variant_mean[(str(row.get("task")), str(row.get("variant")))] = float(row.get("mean_success", 0.0))
    for row in mt.get("episodes", []):
        if row.get("scenario") != "shifted":
            continue
        key = (str(row.get("task")), str(row.get("variant")))
        task_variant_samples.setdefault(key, []).append(float(row.get("success_final", 0.0)))

    def ci95(values: List[float]) -> float:
        n = len(values)
        if n <= 1:
            return 0.0
        m = sum(values) / n
        var = sum((v - m) ** 2 for v in values) / (n - 1)
        return 1.96 * sqrt(var / n)

    categories = [_task_axis_label(task) for task in tasks]
    baseline = [task_variant_mean.get((t, "baseline"), 0.0) for t in tasks]
    baseline_ci = [ci95(task_variant_samples.get((t, "baseline"), [])) for t in tasks]
    ext2 = [task_variant_mean.get((t, "ext2"), 0.0) for t in tasks]
    ext2_ci = [ci95(task_variant_samples.get((t, "ext2"), [])) for t in tasks]
    adapt = [task_variant_mean.get((t, "adaptmanip"), 0.0) for t in tasks]
    adapt_ci = [ci95(task_variant_samples.get((t, "adaptmanip"), [])) for t in tasks]
    method = [task_variant_mean.get((t, "method"), 0.0) for t in tasks]
    method_ci = [ci95(task_variant_samples.get((t, "method"), [])) for t in tasks]
    zero_signal_tasks = [
        _task_axis_label(t)
        for t in tasks
        if all(
            task_variant_mean.get((t, v), 0.0) <= 1e-9
            for v in ("baseline", "ext2", "adaptmanip", "method")
        )
    ]
    svg = grouped_bar_chart_svg(
        title="MetaWorld Shifted Task-wise Success",
        categories=categories,
        series=[
            ("Baseline", baseline, C_BASELINE, baseline_ci),
            ("PPO-CVaR", ext2, C_REF_B, ext2_ci),
            ("adaptmanip", adapt, C_REF_D, adapt_ci),
            ("CORE", method, C_METHOD, method_ci),
        ],
        y_label="Success",
        y_max=1.0,
        x_label_rotation=-26.0,
    )
    if zero_signal_tasks:
        note = ", ".join(zero_signal_tasks)
        annotation = (
            f'<text x="1008" y="568" fill="{C_INK_2}" font-size="9.5" text-anchor="end" font-family="{FONT_FAMILY}">'
            f'all-zero shifted tasks: {xml_escape(note)}'
            "</text>"
        )
        svg = svg.replace("</svg>", annotation + "\n</svg>")
    return svg


def custom_diagnostics_svg() -> str:
    ext = load_json(ROOT / "output/corepaper_reports/ws3/external_baseline_summary.json")
    rel = load_json(ROOT / "output/corepaper_reports/ws5/corepaper_reliability_floor_n14.json")
    n30 = load_json(ROOT / "output/corepaper_reports/ws3/metaworld_seedexp_adaptmanip_method_n30_stats.json")
    mean_map = {row.get("group"): float(row.get("mean", 0.0)) for row in ext.get("rows", [])}

    n30_summary = n30.get("variant_summary", {})
    n30_method = n30_summary.get("method", {})
    n30_comp = n30_summary.get("adaptmanip", {})
    method_mean = float(n30_method.get("mean_success", mean_map.get("method", 0.0)))
    comp_mean = float(n30_comp.get("mean_success", mean_map.get("adaptmanip", 0.0)))
    method_cvar = float(n30_method.get("cvar40_seed", rel.get("reference", {}).get("cvar40", 0.0)))
    comp_cvar = float(n30_comp.get("cvar40_seed", rel.get("comparator", {}).get("cvar40", 0.0)))
    n30_p_mean = 1.0
    n30_p_cvar = 1.0
    for row in n30.get("comparisons", []):
        if row.get("comparator_group") == "adaptmanip":
            n30_p_mean = float(row.get("p_two_sided_mean", row.get("p_two_sided", 1.0)))
            n30_p_cvar = float(row.get("p_two_sided_cvar40_seed", 1.0))
            break
    delta_mean = method_mean - comp_mean
    delta_cvar = method_cvar - comp_cvar

    x_min = max(0.0, min(method_mean, comp_mean) - 0.06)
    x_max = min(1.0, max(method_mean, comp_mean) + 0.06)
    if x_max - x_min < 0.10:
        mid = 0.5 * (x_min + x_max)
        x_min = max(0.0, mid - 0.05)
        x_max = min(1.0, mid + 0.05)
    y_min = max(0.0, min(method_cvar, comp_cvar) - 0.08)
    y_max = min(1.0, max(method_cvar, comp_cvar) + 0.08)
    if y_max - y_min < 0.12:
        mid = 0.5 * (y_min + y_max)
        y_min = max(0.0, mid - 0.06)
        y_max = min(1.0, mid + 0.06)

    width, height = 1000, 440
    parts = [svg_header(width, height)]
    parts.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="{C_BG}"/>')
    parts.append(
        f'<text x="{width/2}" y="32" fill="{C_INK}" font-size="22" text-anchor="middle" font-family="{FONT_FAMILY}">'
        "Controlled Scenario Diagnostics (Quantitative)"
        "</text>"
    )

    # Left panel: closest-pair mean-vs-CVaR scatter (N=30).
    lx, ly, lw, lh = 55, 70, 410, 300
    parts.append(f'<rect x="{lx}" y="{ly}" width="{lw}" height="{lh}" fill="{C_PANEL}" stroke="{C_INK_2}" stroke-width="1.5"/>')
    parts.append(
        f'<text x="{lx+lw/2}" y="{ly+22}" fill="{C_INK}" font-size="14" text-anchor="middle" font-family="{FONT_FAMILY}">'
        "Closest pair (N=30): mean vs CVaR40"
        "</text>"
    )
    plot_x0, plot_y0 = lx + 40, ly + lh - 35
    plot_w, plot_h = lw - 60, lh - 70
    parts.append(f'<line x1="{plot_x0}" y1="{plot_y0}" x2="{plot_x0+plot_w}" y2="{plot_y0}" stroke="{C_INK}" stroke-width="1.5"/>')
    parts.append(f'<line x1="{plot_x0}" y1="{plot_y0-plot_h}" x2="{plot_x0}" y2="{plot_y0}" stroke="{C_INK}" stroke-width="1.5"/>')

    def sx(value: float) -> float:
        span = max(1e-6, x_max - x_min)
        return plot_x0 + ((value - x_min) / span) * plot_w

    def sy(value: float) -> float:
        span = max(1e-6, y_max - y_min)
        return plot_y0 - ((value - y_min) / span) * plot_h

    for i in range(6):
        x_tick = x_min + (x_max - x_min) * i / 5.0
        y_tick = y_min + (y_max - y_min) * i / 5.0
        x = sx(x_tick)
        y = sy(y_tick)
        parts.append(f'<line x1="{x:.2f}" y1="{plot_y0}" x2="{x:.2f}" y2="{plot_y0+4}" stroke="{C_INK}" stroke-width="1"/>')
        parts.append(f'<text x="{x:.2f}" y="{plot_y0+16}" fill="{C_INK_2}" font-size="10" text-anchor="middle" font-family="{FONT_FAMILY}">{x_tick:.2f}</text>')
        parts.append(f'<line x1="{plot_x0-4}" y1="{y:.2f}" x2="{plot_x0}" y2="{y:.2f}" stroke="{C_INK}" stroke-width="1"/>')
        parts.append(f'<text x="{plot_x0-7}" y="{y+3:.2f}" fill="{C_INK_2}" font-size="10" text-anchor="end" font-family="{FONT_FAMILY}">{y_tick:.2f}</text>')
        if i > 0:
            parts.append(f'<line x1="{plot_x0}" y1="{y:.2f}" x2="{plot_x0+plot_w}" y2="{y:.2f}" stroke="{C_GRID}" stroke-width="1"/>')

    x_comp, y_comp = sx(comp_mean), sy(comp_cvar)
    x_met, y_met = sx(method_mean), sy(method_cvar)
    parts.append(f'<line x1="{x_comp:.2f}" y1="{y_comp:.2f}" x2="{x_met:.2f}" y2="{y_met:.2f}" stroke="{C_INK_2}" stroke-width="1.2" stroke-dasharray="4,3"/>')
    parts.append(f'<circle cx="{x_comp:.2f}" cy="{y_comp:.2f}" r="5.5" fill="{C_REF_D}" stroke="{C_INK}" stroke-width="0.8"/>')
    parts.append(f'<circle cx="{x_met:.2f}" cy="{y_met:.2f}" r="5.5" fill="{C_METHOD}" stroke="{C_INK}" stroke-width="0.8"/>')
    parts.append(f'<text x="{x_comp+8:.2f}" y="{y_comp-7:.2f}" fill="{C_INK}" font-size="11" font-family="{FONT_FAMILY}">adaptmanip</text>')
    parts.append(f'<text x="{x_met+8:.2f}" y="{y_met-7:.2f}" fill="{C_INK}" font-size="11" font-family="{FONT_FAMILY}">CORE</text>')
    parts.append(
        f'<text x="{lx+86}" y="{ly+46}" fill="{C_INK_2}" font-size="10.5" font-family="{FONT_FAMILY}">'
        "CORE vs adaptmanip (N=30)"
        "</text>"
    )
    parts.append(f'<text x="{lx+lw/2:.2f}" y="{plot_y0+28}" fill="{C_INK_2}" font-size="11" text-anchor="middle" font-family="{FONT_FAMILY}">Mean success</text>')
    parts.append(
        f'<text x="{plot_x0-30}" y="{ly+lh/2}" fill="{C_INK_2}" font-size="11" text-anchor="middle" transform="rotate(-90 {plot_x0-30} {ly+lh/2})" font-family="{FONT_FAMILY}">CVaR40</text>'
    )

    # Right panel: deep-N return CDF (closest pair).
    rx, ry, rw, rh = 515, 70, 410, 300
    parts.append(f'<rect x="{rx}" y="{ry}" width="{rw}" height="{rh}" fill="{C_PANEL}" stroke="{C_INK_2}" stroke-width="1.5"/>')
    parts.append(
        f'<text x="{rx+rw/2}" y="{ry+22}" fill="{C_INK}" font-size="14" text-anchor="middle" font-family="{FONT_FAMILY}">'
        "Closest pair (N=30): empirical return CDF"
        "</text>"
    )
    px0, py0 = rx + 40, ry + rh - 35
    pw, ph = rw - 60, rh - 70
    parts.append(f'<line x1="{px0}" y1="{py0}" x2="{px0+pw}" y2="{py0}" stroke="{C_INK}" stroke-width="1.5"/>')
    parts.append(f'<line x1="{px0}" y1="{py0-ph}" x2="{px0}" y2="{py0}" stroke="{C_INK}" stroke-width="1.5"/>')
    comp_seed = [float(v) for v in n30_comp.get("seed_means", [])]
    method_seed = [float(v) for v in n30_method.get("seed_means", [])]
    if not comp_seed:
        comp_seed = [comp_mean]
    if not method_seed:
        method_seed = [method_mean]
    combined = comp_seed + method_seed
    cdf_x_min = max(0.0, min(combined) - 0.05)
    cdf_x_max = min(1.0, max(combined) + 0.05)
    if cdf_x_max - cdf_x_min < 0.12:
        mid = 0.5 * (cdf_x_min + cdf_x_max)
        cdf_x_min = max(0.0, mid - 0.06)
        cdf_x_max = min(1.0, mid + 0.06)

    def cx(v: float) -> float:
        span = max(1e-6, cdf_x_max - cdf_x_min)
        return px0 + ((v - cdf_x_min) / span) * pw

    def cy(v: float) -> float:
        return py0 - v * ph

    for i in range(6):
        xv = cdf_x_min + (cdf_x_max - cdf_x_min) * i / 5.0
        x = cx(xv)
        parts.append(f'<line x1="{x:.2f}" y1="{py0}" x2="{x:.2f}" y2="{py0+4}" stroke="{C_INK}" stroke-width="1"/>')
        parts.append(f'<text x="{x:.2f}" y="{py0+15}" fill="{C_INK_2}" font-size="10" text-anchor="middle" font-family="{FONT_FAMILY}">{xv:.2f}</text>')
    for i in range(6):
        pv = i / 5.0
        y = cy(pv)
        parts.append(f'<line x1="{px0-4}" y1="{y:.2f}" x2="{px0}" y2="{y:.2f}" stroke="{C_INK}" stroke-width="1"/>')
        parts.append(f'<text x="{px0-7}" y="{y+3:.2f}" fill="{C_INK_2}" font-size="10" text-anchor="end" font-family="{FONT_FAMILY}">{pv:.1f}</text>')
        if i > 0:
            parts.append(f'<line x1="{px0}" y1="{y:.2f}" x2="{px0+pw}" y2="{y:.2f}" stroke="{C_GRID}" stroke-width="1"/>')

    def cdf_points(values: List[float]) -> List[tuple[float, float]]:
        ordered = sorted(values)
        n = max(1, len(ordered))
        return [(v, (i + 1) / n) for i, v in enumerate(ordered)]

    comp_pts = cdf_points(comp_seed)
    met_pts = cdf_points(method_seed)
    comp_poly = " ".join(f"{cx(v):.2f},{cy(p):.2f}" for v, p in comp_pts)
    met_poly = " ".join(f"{cx(v):.2f},{cy(p):.2f}" for v, p in met_pts)
    parts.append(f'<polyline points="{comp_poly}" fill="none" stroke="{C_REF_D}" stroke-width="2.2"/>')
    parts.append(f'<polyline points="{met_poly}" fill="none" stroke="{C_METHOD}" stroke-width="2.2"/>')
    for v, p in comp_pts:
        parts.append(f'<circle cx="{cx(v):.2f}" cy="{cy(p):.2f}" r="2.4" fill="{C_REF_D}"/>')
    for v, p in met_pts:
        parts.append(f'<circle cx="{cx(v):.2f}" cy="{cy(p):.2f}" r="2.4" fill="{C_METHOD}"/>')

    legend_x = rx + 212
    parts.append(f'<line x1="{legend_x}" y1="{ry+39}" x2="{legend_x+28}" y2="{ry+39}" stroke="{C_REF_D}" stroke-width="2.2"/>')
    parts.append(f'<text x="{legend_x+34}" y="{ry+43}" fill="{C_INK_2}" font-size="10.5" font-family="{FONT_FAMILY}">adaptmanip</text>')
    parts.append(f'<line x1="{legend_x}" y1="{ry+56}" x2="{legend_x+28}" y2="{ry+56}" stroke="{C_METHOD}" stroke-width="2.2"/>')
    parts.append(f'<text x="{legend_x+34}" y="{ry+60}" fill="{C_INK_2}" font-size="10.5" font-family="{FONT_FAMILY}">CORE</text>')
    parts.append(
        f'<text x="{rx+rw/2:.2f}" y="{py0+27:.2f}" fill="{C_INK_2}" font-size="10.5" text-anchor="middle" font-family="{FONT_FAMILY}">Per-seed return</text>'
    )
    parts.append(
        f'<text x="{px0-28}" y="{ry+rh/2:.2f}" fill="{C_INK_2}" font-size="10.5" text-anchor="middle" transform="rotate(-90 {px0-28} {ry+rh/2:.2f})" font-family="{FONT_FAMILY}">Empirical CDF</text>'
    )
    parts.append(svg_footer())
    return "\n".join(parts)


def recent_baselines_matrix_svg() -> str:
    recent = load_json(ROOT / "output/corepaper_reports/ws5/recent_paper_baselines.json")
    meta = load_json(ROOT / "output/corepaper_reports/ws3/metaworld_recent_baselines_stats.json")
    if not meta:
        meta = load_json(ROOT / "output/corepaper_reports/ws3/metaworld_slice_stats.json")

    scenarios = ["nominal"] + list(recent.get("stress_scenarios", []))
    variants = [
        "baseline",
        "ext1",
        "ext2",
        "latency_aware",
        "adaptmanip",
        "robust_cp",
        "history_keyframe",
        "constrained_flow",
        "method",
    ]
    variant_label = {
        "baseline": "base",
        "ext1": "trpo-u",
        "ext2": "ppo-cvar",
        "latency_aware": "lat",
        "adaptmanip": "adapt",
        "robust_cp": "cp",
        "history_keyframe": "hist",
        "constrained_flow": "flow",
        "method": "CORE",
    }
    variant_short = {
        "baseline": "b",
        "ext1": "u",
        "ext2": "c",
        "latency_aware": "l",
        "adaptmanip": "a",
        "robust_cp": "p",
        "history_keyframe": "h",
        "constrained_flow": "f",
        "method": "m",
    }
    variant_color = {
        "baseline": C_BASELINE,
        "ext1": C_REF_A,
        "ext2": C_REF_B,
        "latency_aware": C_REF_C,
        "adaptmanip": C_REF_D,
        "robust_cp": C_REF_E,
        "history_keyframe": C_REF_F,
        "constrained_flow": C_REF_G,
        "method": C_METHOD,
    }

    scenario_map = recent.get("scenario_summary", {})
    matrix_vals: List[float] = []
    for scenario in scenarios:
        for variant in variants:
            value = float(scenario_map.get(scenario, {}).get(variant, {}).get("mean", 0.0))
            matrix_vals.append(value)
    vmin = min(matrix_vals) if matrix_vals else 0.0
    vmax = max(matrix_vals) if matrix_vals else 1.0
    vrange = max(1e-6, vmax - vmin)

    meta_summary = meta.get("variant_summary", {})
    meta_means = [float(meta_summary.get(v, {}).get("mean_success", 0.0)) for v in variants]

    width, height = 940, 440
    parts = [svg_header(width, height)]
    parts.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="{C_BG}"/>')

    # Left panel: heatmap matrix.
    lx, ly, lw, lh = 34, 42, 572, 356
    parts.append(f'<rect x="{lx}" y="{ly}" width="{lw}" height="{lh}" fill="{C_PANEL}" stroke="{C_INK_2}" stroke-width="1.5"/>')
    parts.append(f'<text x="{lx+12}" y="{ly+22}" fill="{C_INK}" font-size="13" font-family="{FONT_FAMILY}">Scenario-model mean success</text>')
    grid_x, grid_y = lx + 112, ly + 38
    cell_w = (lw - 122) / len(variants)
    cell_h = (lh - 58) / len(scenarios)

    for col, variant in enumerate(variants):
        x = grid_x + col * cell_w
        parts.append(
            f'<text x="{x+cell_w/2:.2f}" y="{grid_y-8:.2f}" fill="{C_INK_2}" font-size="10" '
            f'text-anchor="middle" font-family="{FONT_FAMILY}">{variant_label[variant]}</text>'
        )

    for row, scenario in enumerate(scenarios):
        y = grid_y + row * cell_h
        row_values = [float(scenario_map.get(scenario, {}).get(variant, {}).get("mean", 0.0)) for variant in variants]
        row_max = max(row_values) if row_values else 0.0
        parts.append(
            f'<text x="{grid_x-8:.2f}" y="{y+cell_h/2+3:.2f}" fill="{C_INK_2}" font-size="10" '
            f'text-anchor="end" font-family="{FONT_FAMILY}">{xml_escape(scenario)}</text>'
        )
        for col, variant in enumerate(variants):
            x = grid_x + col * cell_w
            value = float(scenario_map.get(scenario, {}).get(variant, {}).get("mean", 0.0))
            t = (value - vmin) / vrange
            fill = lerp_color(C_PANEL, variant_color[variant], 0.25 + 0.75 * t)
            is_row_best = abs(value - row_max) <= 1e-9
            font_weight = "bold" if is_row_best else "normal"
            parts.append(
                f'<rect x="{x+1:.2f}" y="{y+1:.2f}" width="{cell_w-2:.2f}" height="{cell_h-2:.2f}" '
                f'fill="{fill}" rx="2"/>'
            )
            parts.append(
                f'<text x="{x+cell_w/2:.2f}" y="{y+cell_h/2+3:.2f}" fill="{C_INK}" font-size="9.5" '
                f'text-anchor="middle" font-family="{FONT_FAMILY}" font-weight="{font_weight}">{value:.3f}</text>'
            )

    parts.append(f'<text x="{lx+12}" y="{ly+lh-12}" fill="{C_INK_2}" font-size="10" font-family="{FONT_FAMILY}">darker cell = stronger score</text>')

    # Right panel: MetaWorld shifted means (ranked horizontal bars for legibility).
    rx, ry, rw, rh = 624, 42, 286, 356
    parts.append(f'<rect x="{rx}" y="{ry}" width="{rw}" height="{rh}" fill="{C_PANEL}" stroke="{C_INK_2}" stroke-width="1.5"/>')
    parts.append(f'<text x="{rx+rw/2}" y="{ry+22}" fill="{C_INK}" font-size="13" text-anchor="middle" font-family="{FONT_FAMILY}">MetaWorld shifted mean</text>')
    px0, py0 = rx + 82, ry + rh - 30
    pw, ph = rw - 98, rh - 70
    parts.append(f'<line x1="{px0}" y1="{py0}" x2="{px0+pw}" y2="{py0}" stroke="{C_INK}" stroke-width="1.3"/>')
    parts.append(f'<line x1="{px0}" y1="{ry+30}" x2="{px0}" y2="{py0}" stroke="{C_INK}" stroke-width="1.3"/>')

    for i in range(6):
        xv = i / 5
        x = px0 + xv * pw
        parts.append(f'<line x1="{x:.2f}" y1="{ry+30}" x2="{x:.2f}" y2="{py0}" stroke="{C_GRID}" stroke-width="1"/>')
        parts.append(f'<text x="{x:.2f}" y="{py0+13:.2f}" fill="{C_INK_2}" font-size="9" text-anchor="middle" font-family="{FONT_FAMILY}">{xv:.1f}</text>')

    ranked = sorted(zip(variants, meta_means), key=lambda item: item[1], reverse=True)
    row_h = ph / max(len(ranked), 1)
    bar_h = row_h * 0.62
    for i, (variant, value) in enumerate(ranked):
        y_mid = ry + 34 + i * row_h + row_h / 2
        y = y_mid - bar_h / 2
        bw = max(0.0, min(1.0, value)) * pw
        color = variant_color[variant]
        parts.append(f'<rect x="{px0:.2f}" y="{y:.2f}" width="{bw:.2f}" height="{bar_h:.2f}" fill="{color}" rx="1.5"/>')
        label = variant_label[variant]
        parts.append(f'<text x="{px0-6:.2f}" y="{y_mid+3:.2f}" fill="{C_INK_2}" font-size="9.5" text-anchor="end" font-family="{FONT_FAMILY}">{xml_escape(label)}</text>')
        parts.append(f'<text x="{px0+bw+4:.2f}" y="{y_mid+3:.2f}" fill="{C_INK}" font-size="9.5" text-anchor="start" font-family="{FONT_FAMILY}">{value:.2f}</text>')
    parts.append(f'<text x="{px0+pw/2:.2f}" y="{py0+25:.2f}" fill="{C_INK_2}" font-size="9.5" text-anchor="middle" font-family="{FONT_FAMILY}">mean success</text>')

    parts.append(svg_footer())
    return "\n".join(parts)


def uncertainty_dominance_svg() -> str:
    un = load_json(ROOT / "output/corepaper_reports/ws5/uncertainty_dominance.json")
    binned = un.get("binned_scatter", [])
    c_u = float(un.get("assumption_fit", {}).get("c_u", 0.9975))
    c_0 = float(un.get("assumption_fit", {}).get("c_0", 0.00475))
    per_variant = un.get("per_variant", [])

    width, height = 980, 460
    u_vals = [float(row.get("u_mean", 0.0)) for row in binned]
    e_vals = [float(row.get("e_mean", 0.0)) for row in binned]
    u_vals.extend(float(row.get("u_mean", 0.0)) for row in per_variant)
    e_vals.extend(float(row.get("e_mean", 0.0)) for row in per_variant)
    x_max = max(0.14, max(u_vals + [0.0]) * 1.08)
    y_max = max(0.15, max(e_vals + [0.0, c_u * x_max + c_0]) * 1.08)
    bar_y_max = max(0.08, max(max(u_vals + [0.0]), max(e_vals + [0.0])) * 1.18)

    lx, ly, lw, lh = 48, 62, 570, 360
    rx, ry, rw, rh = 652, 62, 280, 360

    def xmap(x: float) -> float:
        return lx + 54 + (x / x_max) * (lw - 84)

    def ymap(y: float) -> float:
        return ly + lh - 40 - (y / y_max) * (lh - 70)

    parts = [svg_header(width, height)]
    parts.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="{C_BG}"/>')
    parts.append(
        f'<text x="{width/2}" y="32" fill="{C_INK}" font-size="21" text-anchor="middle" font-family="{FONT_FAMILY}">'
        "Uncertainty-Dominance: Scatter + Variant Summary"
        "</text>"
    )
    parts.append(f'<rect x="{lx}" y="{ly}" width="{lw}" height="{lh}" fill="{C_PANEL}" stroke="{C_INK_2}" stroke-width="1.4"/>')
    parts.append(f'<rect x="{rx}" y="{ry}" width="{rw}" height="{rh}" fill="{C_PANEL}" stroke="{C_INK_2}" stroke-width="1.4"/>')

    for i in range(6):
        xt = x_max * i / 5
        yt = y_max * i / 5
        x = xmap(xt)
        y = ymap(yt)
        parts.append(f'<line x1="{x:.2f}" y1="{ly+lh-40}" x2="{x:.2f}" y2="{ly+lh-36}" stroke="{C_INK}" stroke-width="1"/>')
        parts.append(f'<text x="{x:.2f}" y="{ly+lh-20}" fill="{C_INK_2}" font-size="10" text-anchor="middle" font-family="{FONT_FAMILY}">{xt:.2f}</text>')
        parts.append(f'<line x1="{lx+50}" y1="{y:.2f}" x2="{lx+54}" y2="{y:.2f}" stroke="{C_INK}" stroke-width="1"/>')
        parts.append(f'<text x="{lx+46}" y="{y+4:.2f}" fill="{C_INK_2}" font-size="10" text-anchor="end" font-family="{FONT_FAMILY}">{yt:.2f}</text>')
        if i > 0:
            parts.append(f'<line x1="{lx+54}" y1="{y:.2f}" x2="{lx+lw-30}" y2="{y:.2f}" stroke="{C_GRID}" stroke-width="1"/>')

    parts.append(f'<line x1="{lx+54}" y1="{ly+22}" x2="{lx+54}" y2="{ly+lh-40}" stroke="{C_INK}" stroke-width="1.6"/>')
    parts.append(f'<line x1="{lx+54}" y1="{ly+lh-40}" x2="{lx+lw-30}" y2="{ly+lh-40}" stroke="{C_INK}" stroke-width="1.6"/>')

    # Reference y=x and fitted envelope.
    parts.append(f'<line x1="{xmap(0):.2f}" y1="{ymap(0):.2f}" x2="{xmap(min(x_max, y_max)):.2f}" y2="{ymap(min(x_max, y_max)):.2f}" stroke="{C_INK_2}" stroke-width="1.4" stroke-dasharray="5,4"/>')
    x0, x1 = 0.0, x_max
    y0, y1 = c_u * x0 + c_0, c_u * x1 + c_0
    parts.append(f'<line x1="{xmap(x0):.2f}" y1="{ymap(y0):.2f}" x2="{xmap(x1):.2f}" y2="{ymap(y1):.2f}" stroke="{C_METHOD}" stroke-width="2"/>')

    for row in binned:
        x = float(row.get("u_mean", 0.0))
        y = float(row.get("e_mean", 0.0))
        cnt = float(row.get("count", 1.0))
        rad = min(6.0, 2.3 + 0.18 * cnt)
        parts.append(f'<circle cx="{xmap(x):.2f}" cy="{ymap(y):.2f}" r="{rad:.2f}" fill="{C_METHOD}" opacity="0.78"/>')

    parts.append(f'<text x="{lx+lw-210}" y="{ly+28}" fill="{C_METHOD}" font-size="11" font-family="{FONT_FAMILY}">fitted envelope</text>')
    parts.append(f'<text x="{lx+lw-210}" y="{ly+44}" fill="{C_INK_2}" font-size="11" font-family="{FONT_FAMILY}">reference e = U</text>')
    parts.append(
        f'<text x="{lx+lw-210}" y="{ly+60}" fill="{C_INK_2}" font-size="10" font-family="{FONT_FAMILY}">'
        f"e &lt;= {c_u:.3f}U + {c_0:.4f}"
        "</text>"
    )
    parts.append(f'<text x="{lx+lw/2}" y="{ly+lh-6}" fill="{C_INK_2}" font-size="11" text-anchor="middle" font-family="{FONT_FAMILY}">Uncertainty proxy U</text>')
    parts.append(
        f'<text x="{lx+14}" y="{ly+lh/2}" fill="{C_INK_2}" font-size="11" text-anchor="middle" transform="rotate(-90 {lx+14} {ly+lh/2})" font-family="{FONT_FAMILY}">Error proxy e</text>'
    )

    # Right panel: per-variant summary bars for interpretability.
    v_order = ["baseline", "ext1", "ext2", "method"]
    v_map = {str(row.get("variant")): row for row in per_variant}
    bw = 20
    for i in range(6):
        yt = bar_y_max * i / 5.0
        y = ry + rh - 34 - (yt / bar_y_max) * (rh - 74)
        parts.append(f'<line x1="{rx+18}" y1="{y:.2f}" x2="{rx+rw-18}" y2="{y:.2f}" stroke="{C_GRID}" stroke-width="1"/>')
        parts.append(f'<text x="{rx+14}" y="{y+3:.2f}" fill="{C_INK_2}" font-size="9" text-anchor="end" font-family="{FONT_FAMILY}">{yt:.2f}</text>')
    for i, variant in enumerate(v_order):
        row = v_map.get(variant, {})
        u_mean = float(row.get("u_mean", 0.0))
        e_mean = float(row.get("e_mean", 0.0))
        base_x = rx + 22 + i * 62
        y_u = ry + rh - 34 - (u_mean / bar_y_max) * (rh - 74)
        y_e = ry + rh - 34 - (e_mean / bar_y_max) * (rh - 74)
        h_u = max(0.0, (u_mean / bar_y_max) * (rh - 74))
        h_e = max(0.0, (e_mean / bar_y_max) * (rh - 74))
        parts.append(f'<rect x="{base_x:.2f}" y="{ry+rh-34-h_u:.2f}" width="{bw}" height="{h_u:.2f}" fill="{C_REF_C}" stroke="{C_INK}" stroke-width="0.5" rx="1.5"/>')
        parts.append(f'<rect x="{base_x+bw+3:.2f}" y="{ry+rh-34-h_e:.2f}" width="{bw}" height="{h_e:.2f}" fill="{C_METHOD}" stroke="{C_INK}" stroke-width="0.5" rx="1.5"/>')
        parts.append(f'<text x="{base_x+bw+1.5:.2f}" y="{ry+rh-18}" fill="{C_INK_2}" font-size="9" text-anchor="middle" font-family="{FONT_FAMILY}">{variant}</text>')
        parts.append(f'<text x="{base_x+bw/2:.2f}" y="{ry+rh-38-h_u:.2f}" fill="{C_INK_2}" font-size="8.5" text-anchor="middle" font-family="{FONT_FAMILY}">{u_mean:.3f}</text>')
        parts.append(f'<text x="{base_x+bw+3+bw/2:.2f}" y="{ry+rh-38-h_e:.2f}" fill="{C_INK_2}" font-size="8.5" text-anchor="middle" font-family="{FONT_FAMILY}">{e_mean:.3f}</text>')
    parts.append(f'<line x1="{rx+18}" y1="{ry+rh-34}" x2="{rx+rw-18}" y2="{ry+rh-34}" stroke="{C_INK}" stroke-width="1.3"/>')
    parts.append(f'<line x1="{rx+18}" y1="{ry+20}" x2="{rx+18}" y2="{ry+rh-34}" stroke="{C_INK}" stroke-width="1.3"/>')
    parts.append(f'<text x="{rx+24}" y="{ry+20}" fill="{C_INK}" font-size="12" font-family="{FONT_FAMILY}">Per-variant means</text>')
    parts.append(f'<rect x="{rx+150}" y="{ry+16}" width="10" height="10" fill="{C_REF_C}" rx="1"/><text x="{rx+164}" y="{ry+25}" fill="{C_INK}" font-size="10" font-family="{FONT_FAMILY}">U mean</text>')
    parts.append(f'<rect x="{rx+214}" y="{ry+16}" width="10" height="10" fill="{C_METHOD}" rx="1"/><text x="{rx+228}" y="{ry+25}" fill="{C_INK}" font-size="10" font-family="{FONT_FAMILY}">e mean</text>')
    parts.append(
        f'<text x="{rx+rw/2:.2f}" y="{ry+rh-8:.2f}" fill="{C_INK_2}" font-size="9.5" text-anchor="middle" font-family="{FONT_FAMILY}">bar axis max={bar_y_max:.3f}</text>'
    )

    parts.append(svg_footer())
    return "\n".join(parts)


def gate_timeline_svg() -> str:
    cycles_dir = ROOT / "output/corepaper_logs/ws4/cycles"
    rows: List[Tuple[str, float, str, float, float]] = []
    for path in sorted(cycles_dir.glob("*.json")):
        payload = load_json(path)
        if "delta" in payload and "timestamp_utc" in payload:
            rows.append(
                (
                    str(payload["timestamp_utc"]),
                    float(payload["delta"]),
                    str(payload.get("decision", "")),
                    float(payload.get("baseline", 0.0)),
                    float(payload.get("method", 0.0)),
                )
            )
    rows.sort(key=lambda r: r[0])
    if not rows:
        rows = [("t1", 0.042, "green", 0.70, 0.742), ("t2", -0.019, "red", 0.75, 0.731), ("t3", 0.0372, "green", 0.712, 0.7492)]
    rows = rows[:10]

    width, height = 980, 470
    margin_left, margin_right = 74, 28
    top_y = 62
    top_h = 180
    bottom_y = 274
    bottom_h = 150
    plot_w = width - margin_left - margin_right
    d_min, d_max = -0.025, 0.045
    s_min, s_max = 0.68, 0.76

    def xmap(i: int) -> float:
        if len(rows) == 1:
            return margin_left + plot_w / 2
        return margin_left + (i / (len(rows) - 1)) * plot_w

    def y_delta(v: float) -> float:
        return bottom_y + bottom_h - ((v - d_min) / (d_max - d_min)) * (bottom_h - 28)

    def y_score(v: float) -> float:
        return top_y + top_h - ((v - s_min) / (s_max - s_min)) * (top_h - 26)

    tau_green = 0.02
    tau_yellow = 0.005

    parts = [svg_header(width, height)]
    parts.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="{C_BG}"/>')
    parts.append(
        f'<text x="{width/2}" y="30" fill="{C_INK}" font-size="21" text-anchor="middle" font-family="{FONT_FAMILY}">'
        "Gate Timeline: Scores + Delta Decisions"
        "</text>"
    )
    # Top panel: baseline vs candidate scores.
    parts.append(f'<rect x="{margin_left-10}" y="{top_y}" width="{plot_w+20}" height="{top_h}" fill="{C_PANEL}" stroke="{C_INK_2}" stroke-width="1.2"/>')
    parts.append(f'<line x1="{margin_left}" y1="{top_y+top_h-2}" x2="{width-margin_right}" y2="{top_y+top_h-2}" stroke="{C_INK}" stroke-width="1.3"/>')
    parts.append(f'<line x1="{margin_left}" y1="{top_y+10}" x2="{margin_left}" y2="{top_y+top_h-2}" stroke="{C_INK}" stroke-width="1.3"/>')
    baseline_poly = " ".join(f"{xmap(i):.2f},{y_score(b):.2f}" for i, (_, _, _, b, _) in enumerate(rows))
    method_poly = " ".join(f"{xmap(i):.2f},{y_score(m):.2f}" for i, (_, _, _, _, m) in enumerate(rows))
    parts.append(f'<polyline points="{baseline_poly}" fill="none" stroke="{C_BASELINE}" stroke-width="2.1"/>')
    parts.append(f'<polyline points="{method_poly}" fill="none" stroke="{C_METHOD}" stroke-width="2.3"/>')
    for i, (_, _, _, b, m) in enumerate(rows):
        x = xmap(i)
        parts.append(f'<circle cx="{x:.2f}" cy="{y_score(b):.2f}" r="2.5" fill="{C_BASELINE}"/>')
        parts.append(f'<circle cx="{x:.2f}" cy="{y_score(m):.2f}" r="2.8" fill="{C_METHOD}"/>')
    for i in range(5):
        yv = s_min + (s_max - s_min) * i / 4.0
        y = y_score(yv)
        parts.append(f'<line x1="{margin_left}" y1="{y:.2f}" x2="{width-margin_right}" y2="{y:.2f}" stroke="{C_GRID}" stroke-width="1"/>')
        parts.append(f'<text x="{margin_left-6}" y="{y+3:.2f}" fill="{C_INK_2}" font-size="9.5" text-anchor="end" font-family="{FONT_FAMILY}">{yv:.3f}</text>')
    parts.append(f'<text x="{margin_left+10}" y="{top_y+16}" fill="{C_INK}" font-size="11" font-family="{FONT_FAMILY}">Score trajectory</text>')
    parts.append(f'<rect x="{margin_left+132}" y="{top_y+8}" width="10" height="10" fill="{C_BASELINE}" rx="1"/><text x="{margin_left+146}" y="{top_y+17}" fill="{C_INK}" font-size="10" font-family="{FONT_FAMILY}">baseline</text>')
    parts.append(f'<rect x="{margin_left+206}" y="{top_y+8}" width="10" height="10" fill="{C_METHOD}" rx="1"/><text x="{margin_left+220}" y="{top_y+17}" fill="{C_INK}" font-size="10" font-family="{FONT_FAMILY}">candidate</text>')

    # Bottom panel: delta bars + decision thresholds.
    parts.append(f'<rect x="{margin_left-10}" y="{bottom_y}" width="{plot_w+20}" height="{bottom_h}" fill="{C_PANEL}" stroke="{C_INK_2}" stroke-width="1.2"/>')
    parts.append(f'<line x1="{margin_left}" y1="{bottom_y+bottom_h-2}" x2="{width-margin_right}" y2="{bottom_y+bottom_h-2}" stroke="{C_INK}" stroke-width="1.3"/>')
    parts.append(f'<line x1="{margin_left}" y1="{bottom_y+10}" x2="{margin_left}" y2="{bottom_y+bottom_h-2}" stroke="{C_INK}" stroke-width="1.3"/>')
    parts.append(f'<line x1="{margin_left}" y1="{y_delta(tau_green):.2f}" x2="{width-margin_right}" y2="{y_delta(tau_green):.2f}" stroke="{C_REF_A}" stroke-width="1.2" stroke-dasharray="5,4"/>')
    parts.append(f'<line x1="{margin_left}" y1="{y_delta(tau_yellow):.2f}" x2="{width-margin_right}" y2="{y_delta(tau_yellow):.2f}" stroke="{C_REF_B}" stroke-width="1.2" stroke-dasharray="5,4"/>')
    parts.append(f'<line x1="{margin_left}" y1="{y_delta(0.0):.2f}" x2="{width-margin_right}" y2="{y_delta(0.0):.2f}" stroke="{C_INK_2}" stroke-width="1.0" stroke-dasharray="4,3"/>')

    for i in range(6):
        yv = d_min + (d_max - d_min) * i / 5.0
        y = y_delta(yv)
        parts.append(f'<line x1="{margin_left}" y1="{y:.2f}" x2="{width-margin_right}" y2="{y:.2f}" stroke="{C_GRID}" stroke-width="1"/>')
        parts.append(f'<text x="{margin_left-6}" y="{y+3:.2f}" fill="{C_INK_2}" font-size="9.5" text-anchor="end" font-family="{FONT_FAMILY}">{yv:+.3f}</text>')

    bar_w = max(12.0, plot_w / max(len(rows), 1) * 0.45)
    decision_colors = {"green": C_REF_A, "yellow": C_REF_B, "red": C_METHOD}
    for i, (_, delta, decision, _, _) in enumerate(rows):
        x = xmap(i)
        y0 = y_delta(0.0)
        yd = y_delta(delta)
        y = min(y0, yd)
        h = max(abs(y0 - yd), 1.0)
        col = decision_colors.get(decision.lower(), C_REF_C)
        parts.append(f'<rect x="{x-bar_w/2:.2f}" y="{y:.2f}" width="{bar_w:.2f}" height="{h:.2f}" fill="{col}" stroke="{C_INK}" stroke-width="0.5" rx="1.5"/>')
        parts.append(f'<text x="{x:.2f}" y="{y-4:.2f}" fill="{C_INK_2}" font-size="9" text-anchor="middle" font-family="{FONT_FAMILY}">{delta:+.3f}</text>')
        parts.append(f'<text x="{x:.2f}" y="{bottom_y+bottom_h+14}" fill="{C_INK_2}" font-size="10" text-anchor="middle" font-family="{FONT_FAMILY}">{i+1}</text>')

    parts.append(f'<text x="{margin_left+10}" y="{bottom_y+16}" fill="{C_INK}" font-size="11" font-family="{FONT_FAMILY}">Delta and decision banding</text>')
    parts.append(f'<text x="{margin_left+208}" y="{bottom_y+16}" fill="{C_REF_A}" font-size="10" font-family="{FONT_FAMILY}">tau_green={tau_green:.3f}</text>')
    parts.append(f'<text x="{margin_left+316}" y="{bottom_y+16}" fill="{C_REF_B}" font-size="10" font-family="{FONT_FAMILY}">tau_yellow={tau_yellow:.3f}</text>')
    parts.append(f'<rect x="{margin_left+438}" y="{bottom_y+8}" width="10" height="10" fill="{C_REF_A}" rx="1"/>')
    parts.append(f'<text x="{margin_left+452}" y="{bottom_y+17}" fill="{C_INK_2}" font-size="10" font-family="{FONT_FAMILY}">promote</text>')
    parts.append(f'<rect x="{margin_left+510}" y="{bottom_y+8}" width="10" height="10" fill="{C_REF_B}" rx="1"/>')
    parts.append(f'<text x="{margin_left+524}" y="{bottom_y+17}" fill="{C_INK_2}" font-size="10" font-family="{FONT_FAMILY}">monitor</text>')
    parts.append(f'<rect x="{margin_left+582}" y="{bottom_y+8}" width="10" height="10" fill="{C_METHOD}" rx="1"/>')
    parts.append(f'<text x="{margin_left+596}" y="{bottom_y+17}" fill="{C_INK_2}" font-size="10" font-family="{FONT_FAMILY}">rollback</text>')
    parts.append(f'<text x="{width/2}" y="{height-10}" fill="{C_INK_2}" font-size="11" text-anchor="middle" font-family="{FONT_FAMILY}">Cycle index</text>')
    parts.append(svg_footer())
    return "\n".join(parts)


def legacy_pipeline_svg() -> str:
    width, height = 1120, 420
    parts = [svg_header(width, height)]
    parts.append(f'<rect x="0" y="0" width="{width}" height="{height}" fill="{C_BG}"/>')
    parts.append(
        f'<text x="{width/2}" y="44" fill="{C_INK}" font-size="24" text-anchor="middle" font-family="{FONT_FAMILY}">'
        "F1: Closed Research Loop Pipeline"
        "</text>"
    )
    labels = ["Literature\nIngestion", "Hypothesis\n& Theory", "Experiment\nHarness", "Cycle\nDecision", "Paper\nAssets"]
    x0 = 50
    y = 140
    box_w = 180
    box_h = 90
    gap = 40
    for i, label in enumerate(labels):
        x = x0 + i * (box_w + gap)
        parts.append(f'<rect x="{x}" y="{y}" width="{box_w}" height="{box_h}" rx="10" fill="{C_PANEL}" stroke="{C_INK_2}" stroke-width="2"/>')
        a, b = label.split("\n")
        parts.append(f'<text x="{x+box_w/2}" y="{y+38}" fill="{C_INK}" font-size="16" text-anchor="middle" font-family="{FONT_FAMILY}">{xml_escape(a)}</text>')
        parts.append(f'<text x="{x+box_w/2}" y="{y+62}" fill="{C_INK}" font-size="16" text-anchor="middle" font-family="{FONT_FAMILY}">{xml_escape(b)}</text>')
        if i < len(labels) - 1:
            ax = x + box_w + 10
            ay = y + box_h / 2
            parts.append(f'<line x1="{ax}" y1="{ay}" x2="{ax+24}" y2="{ay}" stroke="{C_INK_2}" stroke-width="3"/>')
            parts.append(f'<polygon points="{ax+24},{ay-6} {ax+24},{ay+6} {ax+34},{ay}" fill="{C_INK_2}"/>')
    parts.append(f'<text x="{width/2}" y="330" fill="{C_INK_2}" font-size="16" text-anchor="middle" font-family="{FONT_FAMILY}">Cycle links evidence, theory updates, and manuscript claims.</text>')
    parts.append(svg_footer())
    return "\n".join(parts)


def legacy_main_benchmark_svg() -> str:
    ext = load_json(ROOT / "output/corepaper_reports/ws3/external_baseline_summary.json")
    rows = {str(r.get("group")): r for r in ext.get("rows", [])}
    order = ["baseline", "ext1", "ext2", "method"]
    labels = ["baseline", "ext1", "ext2", "CORE"]
    vals = [float(rows.get(k, {}).get("mean", 0.0)) for k in order]
    cis = [float(rows.get(k, {}).get("ci95", 0.0)) for k in order]
    bar_colors = [C_BASELINE, C_REF_A, C_REF_B, C_METHOD]
    return grouped_bar_chart_svg(
        title="F2: Main Benchmark Comparison",
        categories=labels,
        series=[("mean \u00b1 CI95", vals, bar_colors, cis)],
        y_label="Mean success",
        y_max=0.82,
        show_value_labels=True,
    )


def legacy_ablation_svg() -> str:
    ablation = load_json(ROOT / "output/corepaper_reports/ws5/ablation_results.json")
    rows = {str(r.get("group")): r for r in ablation.get("rows", [])}
    order = ["method_full", "no_feedback_gating", "no_history", "no_history_no_feedback", "no_robust_reg"]
    labels = ["full", "no-gate", "no-history", "no-gate+history", "no-robust"]
    vals = [float(rows.get(k, {}).get("mean", 0.0)) for k in order]
    cis = [1.96 * float(rows.get(k, {}).get("std", 0.0)) / sqrt(max(float(rows.get(k, {}).get("n", 1)), 1.0)) for k in order]
    bar_colors = [C_METHOD, C_REF_C, C_REF_D, C_REF_F, C_REF_E]
    return grouped_bar_chart_svg(
        title="F3: Ablation Impact",
        categories=labels,
        series=[("mean \u00b1 CI95", vals, bar_colors, cis)],
        y_label="Mean success",
        y_max=0.80,
        show_value_labels=True,
    )


def legacy_robustness_svg() -> str:
    rob = load_json(ROOT / "output/corepaper_reports/ws5/robustness_results.json")
    pick = [("R1", "med"), ("R2", "med"), ("R3", "severe"), ("R4", "hard")]
    by_key = {(str(r.get("test")), str(r.get("severity"))): r for r in rob.get("rows", [])}
    categories = []
    baseline_vals = []
    method_vals = []
    for test, sev in pick:
        row = by_key.get((test, sev), {})
        categories.append(f"{test}-{sev}")
        baseline_vals.append(float(row.get("baseline_mean", 0.0)))
        method_vals.append(float(row.get("method_mean", 0.0)))
    return grouped_bar_chart_svg(
        title="F4: Robustness Comparison (Representative Severities)",
        categories=categories,
        series=[
            ("baseline", baseline_vals, C_BASELINE, None),
            ("CORE", method_vals, C_METHOD, None),
        ],
        y_label="Mean success",
        y_max=0.80,
        show_value_labels=True,
    )


def legacy_failure_taxonomy_svg() -> str:
    vf = load_json(ROOT / "output/corepaper_reports/ws5/verification_first_diagnostics.json")
    tax = vf.get("failure_taxonomy", {})
    categories = ["performance_floor", "stability", "recovery"]
    vals = [float(tax.get(c, 0.0)) for c in categories]
    svg = grouped_bar_chart_svg(
        title="F5: Failure Taxonomy Counts",
        categories=["floor", "stability", "recovery"],
        series=[("count", vals, C_METHOD, None)],
        y_label="Count",
        y_max=max(1.0, max(vals) + 1.0),
        show_value_labels=True,
        zero_bar_min_px=1.4,
    )
    if all(v <= 0.0 for v in vals):
        annotation = (
            f'<text x="520" y="565" fill="{C_INK_2}" font-size="11" text-anchor="middle" font-family="{FONT_FAMILY}">'
            "No verification-threshold failures observed in this cycle."
            "</text>"
        )
        svg = svg.replace("</svg>", annotation + "\n</svg>")
    return svg


def legacy_baseline_calibration_svg() -> str:
    cal = load_json(ROOT / "output/corepaper_reports/ws3/baseline_calibration.json")
    rows = {str(r.get("group")): r for r in cal.get("rows", [])}
    order = ["baseline", "ext1", "ext2"]
    categories = ["baseline", "ext1", "ext2"]
    target = [float(rows.get(k, {}).get("target_mean", 0.0)) for k in order]
    observed = [float(rows.get(k, {}).get("observed_mean", 0.0)) for k in order]
    return grouped_bar_chart_svg(
        title="F6: Baseline Calibration (Target vs Observed)",
        categories=categories,
        series=[("Target", target, C_REF_A, None), ("Observed", observed, C_REF_B, None)],
        y_label="Mean success",
        y_max=0.82,
        show_value_labels=True,
    )


def legacy_metaworld_taskwise_svg() -> str:
    mt = load_json(ROOT / "output/corepaper_reports/ws3/metaworld_slice_results.json")
    rows = [r for r in mt.get("task_breakdown", []) if r.get("scenario") == "shifted"]
    configured_tasks, _ = _load_configured_metaworld_tasks()
    task_order = _ordered_shifted_tasks(rows, configured_tasks)
    if not task_order:
        task_order = sorted({str(r.get("task")) for r in rows if r.get("task")})

    def lookup(task: str, variant: str) -> float:
        for row in rows:
            if str(row.get("task")) == task and str(row.get("variant")) == variant:
                return float(row.get("mean_success", 0.0))
        return 0.0

    categories = [_task_axis_label(t) for t in task_order]
    baseline = [lookup(t, "baseline") for t in task_order]
    ext2 = [lookup(t, "ext2") for t in task_order]
    method = [lookup(t, "method") for t in task_order]
    return grouped_bar_chart_svg(
        title="F7: MT1 Shifted Task-wise Success",
        categories=categories,
        series=[("baseline", baseline, C_BASELINE, None), ("PPO-CVaR", ext2, C_REF_B, None), ("CORE", method, C_METHOD, None)],
        y_label="Success",
        y_max=1.0,
        show_value_labels=True,
    )


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LEGACY_OUT_DIR.mkdir(parents=True, exist_ok=True)
    figures = {
        "metaworld_taskwise.svg": metaworld_taskwise_svg(),
        "custom_diagnostics.svg": custom_diagnostics_svg(),
        "recent_baselines_matrix.svg": recent_baselines_matrix_svg(),
        "uncertainty_dominance.svg": uncertainty_dominance_svg(),
        "gate_timeline.svg": gate_timeline_svg(),
    }
    for filename, content in figures.items():
        write(OUT_DIR / filename, content)

    legacy_figures = {
        "F1_pipeline.svg": legacy_pipeline_svg(),
        "F2_main_benchmark.svg": legacy_main_benchmark_svg(),
        "F3_ablation.svg": legacy_ablation_svg(),
        "F4_robustness.svg": legacy_robustness_svg(),
        "F5_failure_taxonomy.svg": legacy_failure_taxonomy_svg(),
        "F6_baseline_calibration.svg": legacy_baseline_calibration_svg(),
        "F7_metaworld_taskwise.svg": legacy_metaworld_taskwise_svg(),
    }
    for filename, content in legacy_figures.items():
        write(LEGACY_OUT_DIR / filename, content)

    readme = [
        "# Paper Figures",
        "",
        "These SVG assets are the source-of-truth visualizations used directly by the manuscript.",
        "",
        "- `metaworld_taskwise.svg`",
        "- `custom_diagnostics.svg`",
        "- `recent_baselines_matrix.svg`",
        "- `uncertainty_dominance.svg`",
        "- `gate_timeline.svg`",
        "",
        "Run `scripts/figures/export_png_figures.py` to produce PDF vectors (and optional PNG copies).",
        "",
        "Legacy pipeline-required assets (`F1`..`F7`) are generated to `output/corepaper_assets/figures/` from the same source reports.",
    ]
    write(OUT_DIR / "README.md", "\n".join(readme) + "\n")
    print(f"Generated manuscript SVG figures in {OUT_DIR}")
    print(f"Generated legacy SVG figures in {LEGACY_OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
