#!/usr/bin/env python3
"""Apply recurring council feedback actions to paper text/figures (idempotent)."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_actions(council: dict) -> list[str]:
    out: list[str] = []
    for row in council.get("consensus_actions", []):
        if isinstance(row, str) and row.strip():
            out.append(row.strip())
    return out


def sanitize_abstract_no_exact_pvals(text: str) -> tuple[str, bool]:
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", text, flags=re.S)
    if not m:
        return text, False
    block = m.group(1)
    # Remove explicit p-value snippets in abstract only.
    new_block = re.sub(r"\s*\(\$p=.*?\)", "", block)
    if new_block == block:
        return text, False
    return text[: m.start(1)] + new_block + text[m.end(1) :], True


def ensure_rollout_sampling_sentence(text: str) -> tuple[str, bool]:
    needle = (
        "Here \\widetilde{\\mathcal{B}}_k(\\theta) is a short candidate-policy rollout batch "
        "produced by the current world-model snapshot \\phi_k"
    )
    wanted = (
        "Here \\widetilde{\\mathcal{B}}_k(\\theta) is a short candidate-policy rollout batch "
        "produced by the current world-model snapshot \\phi_k from a seed-matched minibatch of "
        "incumbent replay start states; gating does not require deployment execution of the candidate policy."
    )
    if wanted in text:
        return text, False
    if needle in text:
        text = text.replace(
            "Here \\widetilde{\\mathcal{B}}_k(\\theta) is a short candidate-policy rollout batch produced by the current world-model snapshot \\phi_k from states sampled from the incumbent replay distribution; gating does not require deployment execution of the candidate policy.",
            wanted,
        )
        return text, True
    return text, False


def enforce_proposition_framing(text: str) -> tuple[str, bool]:
    changed = False
    new = text
    if "\\newtheorem{theorem}{Theorem}" in new:
        new = new.replace("\\newtheorem{theorem}{Theorem}\n", "")
        changed = True
    if "\\begin{theorem}" in new or "\\end{theorem}" in new:
        new = new.replace("\\begin{theorem}", "\\begin{proposition}")
        new = new.replace("\\end{theorem}", "\\end{proposition}")
        changed = True
    return new, changed


def ensure_power_table_reference(text: str) -> tuple[str, bool]:
    if "Table~\\ref{tab:latency-power}" in text:
        return text, False
    marker = "The deep closest-pair mean effect size is small"
    idx = text.find(marker)
    if idx < 0:
        return text, False
    insert = (
        "Table~\\ref{tab:latency-power} reports the corresponding detection-power regime for this closest-pair comparison. "
    )
    return text[:idx] + insert + text[idx:], True


def ensure_official_lane_prominent(text: str) -> tuple[str, bool]:
    sent = (
        "Fairness anchors from the official-library lane remain favorable for CORE "
        "(\\CoreLibLaneMethodMean\\ mean vs \\CoreLibLaneSbThreeMean\\ for SB3 PPO and "
        "\\CoreLibLaneRllibMean\\ for RLlib SAC; $p=\\CoreLibLanePSbThree,\\CoreLibLanePRllib$)."
    )
    if sent in text:
        return text, False
    marker = "CVaR-alpha sensitivity on the \\texttt{latency\\_aware} slice remains favorable for CORE"
    idx = text.find(marker)
    if idx < 0:
        return text, False
    return text[:idx] + sent + " " + text[idx:], True


def ensure_histogram_numeric_labels(fig_text: str) -> tuple[str, bool]:
    changed = False
    new = fig_text
    old = 'parts.append(f\'<text x="{gx+group_w/2:.2f}" y="{py0+14:.2f}" fill="{C_INK_2}" font-size="10" text-anchor="middle" font-family="{FONT_FAMILY}">B{i+1}</text>\')'
    if old in new:
        repl = (
            "        label = bin_labels[i] if i < len(bin_labels) else f\"B{i+1}\"\n"
            "        parts.append(f'<text x=\"{gx+group_w/2:.2f}\" y=\"{py0+14:.2f}\" fill=\"{C_INK_2}\" font-size=\"8.8\" text-anchor=\"middle\" font-family=\"{FONT_FAMILY}\">{label}</text>')"
        )
        new = new.replace(old, repl)
        changed = True
    return new, changed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--council-json", type=Path, required=True)
    ap.add_argument("--paper-tex", type=Path, default=Path("paper/manuscript.tex"))
    ap.add_argument("--fig-script", type=Path, default=Path("scripts/figures/generate_paper_figures.py"))
    args = ap.parse_args()

    council = load_json(args.council_json)
    actions = [a.lower() for a in parse_actions(council)]

    paper = args.paper_tex.read_text(encoding="utf-8")
    fig = args.fig_script.read_text(encoding="utf-8")

    changed_paper = False
    changed_fig = False

    if any("convert theorem" in a and "proposition" in a for a in actions):
        paper, ch = enforce_proposition_framing(paper)
        changed_paper = changed_paper or ch

    if any("remove exact p-values" in a or "abstract" in a and "dense" in a for a in actions):
        paper, ch = sanitize_abstract_no_exact_pvals(paper)
        changed_paper = changed_paper or ch

    if any("rollout batch" in a or "sampling text" in a for a in actions):
        paper, ch = ensure_rollout_sampling_sentence(paper)
        changed_paper = changed_paper or ch

    if any("power" in a and "table" in a for a in actions):
        paper, ch = ensure_power_table_reference(paper)
        changed_paper = changed_paper or ch

    if any("official-library lane" in a or "official upstream" in a for a in actions):
        paper, ch = ensure_official_lane_prominent(paper)
        changed_paper = changed_paper or ch

    if any("x-axis" in a and "bin" in a for a in actions):
        fig, ch = ensure_histogram_numeric_labels(fig)
        changed_fig = changed_fig or ch

    if changed_paper:
        args.paper_tex.write_text(paper, encoding="utf-8")
    if changed_fig:
        args.fig_script.write_text(fig, encoding="utf-8")

    print(
        json.dumps(
            {
                "changed_paper": changed_paper,
                "changed_fig_script": changed_fig,
                "actions": actions,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
