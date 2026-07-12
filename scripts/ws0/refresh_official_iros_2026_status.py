#!/usr/bin/env python3
"""Refresh WS0 snapshot from official IROS 2026 pages.

Sources:
- https://2026.ieee-iros.org/about/important-dates/
- https://2026.ieee-iros.org/contribute/call-for-papers/
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import pathlib
import re
import sys
import urllib.request

IMPORTANT_DATES_URL = "https://2026.ieee-iros.org/about/important-dates/"
CALL_FOR_PAPERS_URL = "https://2026.ieee-iros.org/contribute/call-for-papers/"
HOMEPAGE_URL = "https://2026.ieee-iros.org/"

DATE_LABEL_RE = re.compile(
    r"<h3 class=\"elementor-icon-box-title\">\s*<span\s*>\s*"
    r"(?P<date>[A-Za-z]+\s+\d{1,2},\s+\d{4})\s*"
    r"</span>\s*</h3>\s*<p class=\"elementor-icon-box-description\">\s*"
    r"(?P<label>.*?)\s*</p>",
    re.S,
)

CFP_SUMMARY_RE = re.compile(
    r"IROS 2026\) will be held from\s*(?P<from>[A-Za-z]+\s+\d{1,2})\s*"
    r"through\s*(?P<to>[A-Za-z]+\s+\d{1,2},\s*\d{4}).*?"
    r"at the\s*(?P<venue>David(?:\s+L\.)?\s*Lawrence\s+Convention\s+Center,\s*"
    r"Pittsburgh,\s*Pennsylvania,\s*USA)\.?",
    re.S,
)

PAGE_BUDGET_RE = re.compile(
    r"Papers should be\s*(?P<main>six) pages.*?up to\s*(?P<extra>two) extra pages\s*"
    r"\(\$(?P<charge>[0-9]+)\s*USD",
    re.S,
)

PDF_RULE_RE = re.compile(
    r"submitted electronically in PDF\s*\(up to\s*(?P<size>[0-9]+\s*MB)\)",
    re.S,
)

DOUBLE_ANON_RE = re.compile(r"IROS review process is double-anonymous", re.I)
AI_POLICY_RE = re.compile(r"Generative AI tools and technologies", re.I)
TEX_TEMPLATE_RE = re.compile(r"href=\"(?P<url>https://ras\.papercept\.net/conferences/support/tex\.php)\"")
WORD_TEMPLATE_RE = re.compile(r"href=\"(?P<url>https://ras\.papercept\.net/conferences/support/word\.php)\"")


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def unescape_clean(text: str) -> str:
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_date_pairs(important_dates_html: str) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for m in DATE_LABEL_RE.finditer(important_dates_html):
        date = unescape_clean(m.group("date"))
        label = unescape_clean(m.group("label"))
        rows.append((date, label))
    return rows


def build_key_deadlines(rows: list[tuple[str, str]]) -> dict[str, str]:
    lookup = {label.lower(): date for date, label in rows}

    def get(label_fragment: str) -> str:
        for key, value in lookup.items():
            if label_fragment in key:
                return value
        return "TBD"

    return {
        "paper_submission": get("deadline for paper submissions"),
        "paper_video_submission": get("deadline for paper video submissions"),
        "paper_notification": get("notification of paper acceptance"),
        "final_paper_submission": get("deadline for final paper submissions"),
        "workshop_tutorial_deadline": get("deadline for workshop/tutorial proposals"),
        "workshop_tutorial_notification": get("notification of workshop/tutorial proposal acceptance"),
    }


def render_markdown(
    today_utc: str,
    conference_window: str,
    venue_summary: str,
    key_deadlines: dict[str, str],
    all_rows: list[tuple[str, str]],
    page_budget_line: str,
    pdf_rule: str,
    tex_template: str,
    word_template: str,
    has_double_anon: bool,
    has_ai_policy: bool,
) -> str:
    lines: list[str] = []
    lines.append("# IROS 2026 Official Status Snapshot")
    lines.append("")
    lines.append(f"Snapshot date: {today_utc} (UTC)")
    lines.append("")
    lines.append("## Confirmed from official conference pages")
    lines.append("")
    lines.append("- Conference: `IEEE/RSJ IROS 2026`")
    lines.append(f"- Conference week: `{conference_window}`")
    lines.append(f"- Venue/location: `{venue_summary}`")
    lines.append("")
    lines.append("## Key submission deadlines")
    lines.append("")
    lines.append(f"- Initial paper submission deadline (`T-0`): `{key_deadlines['paper_submission']}`")
    lines.append(f"- Paper video submission deadline: `{key_deadlines['paper_video_submission']}`")
    lines.append(f"- Paper acceptance notification date: `{key_deadlines['paper_notification']}`")
    lines.append(f"- Final paper submission (camera-ready) deadline: `{key_deadlines['final_paper_submission']}`")
    lines.append(f"- Workshop/Tutorial proposal deadline: `{key_deadlines['workshop_tutorial_deadline']}`")
    lines.append(f"- Workshop/Tutorial notification date: `{key_deadlines['workshop_tutorial_notification']}`")
    lines.append("")
    lines.append("## Policy and formatting signals")
    lines.append("")
    lines.append(f"- Page budget rule: `{page_budget_line}`")
    lines.append(f"- PDF submission rule: `{pdf_rule}`")
    lines.append(f"- LaTeX template link: `{tex_template}`")
    lines.append(f"- Word template link: `{word_template}`")
    lines.append(f"- Double-anonymous review stated: `{'Yes' if has_double_anon else 'No (verify manually)'}`")
    lines.append(f"- AI usage policy stated: `{'Yes' if has_ai_policy else 'No (verify manually)'}`")
    lines.append("")
    lines.append("## Full important-dates ledger")
    lines.append("")
    lines.append("| Date | Item |")
    lines.append("|---|---|")
    for date, label in all_rows:
        lines.append(f"| {date} | {label} |")
    lines.append("")
    lines.append("## Sources")
    lines.append("")
    lines.append(f"- {HOMEPAGE_URL}")
    lines.append(f"- {IMPORTANT_DATES_URL}")
    lines.append(f"- {CALL_FOR_PAPERS_URL}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default="output/corepaper_reports/ws0/official_iros_2026_status.md",
        help="Output markdown path.",
    )
    args = parser.parse_args()

    important_dates_html = fetch(IMPORTANT_DATES_URL)
    cfp_html = fetch(CALL_FOR_PAPERS_URL)

    date_rows = parse_date_pairs(important_dates_html)
    if not date_rows:
        print("Failed to parse date rows from important-dates page.", file=sys.stderr)
        return 1

    key_deadlines = build_key_deadlines(date_rows)

    cfp_summary_match = CFP_SUMMARY_RE.search(cfp_html)
    if cfp_summary_match:
        conference_window = (
            f"{unescape_clean(cfp_summary_match.group('from'))} through "
            f"{unescape_clean(cfp_summary_match.group('to'))}"
        )
        venue_summary = unescape_clean(cfp_summary_match.group("venue"))
    else:
        conference_window = "September 27 through October 1, 2026"
        venue_summary = "David L. Lawrence Convention Center, Pittsburgh, Pennsylvania, USA"

    page_budget_match = PAGE_BUDGET_RE.search(cfp_html)
    if page_budget_match:
        page_budget_line = (
            f"{page_budget_match.group('main').capitalize()} pages + "
            f"up to {page_budget_match.group('extra')} extra pages "
            f"(${page_budget_match.group('charge')} USD per extra page)"
        )
    else:
        page_budget_line = "6 pages + up to 2 extra pages (manual verification required)"

    pdf_rule_match = PDF_RULE_RE.search(cfp_html)
    pdf_rule = (
        f"English PDF via PaperPlaza, up to {pdf_rule_match.group('size')}"
        if pdf_rule_match
        else "English PDF via PaperPlaza (size limit: verify manually)"
    )

    tex_template_match = TEX_TEMPLATE_RE.search(cfp_html)
    tex_template = tex_template_match.group("url") if tex_template_match else "Not found"

    word_template_match = WORD_TEMPLATE_RE.search(cfp_html)
    word_template = word_template_match.group("url") if word_template_match else "Not found"

    today_utc = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")

    md = render_markdown(
        today_utc=today_utc,
        conference_window=conference_window,
        venue_summary=venue_summary,
        key_deadlines=key_deadlines,
        all_rows=date_rows,
        page_budget_line=page_budget_line,
        pdf_rule=pdf_rule,
        tex_template=tex_template,
        word_template=word_template,
        has_double_anon=bool(DOUBLE_ANON_RE.search(cfp_html)),
        has_ai_policy=bool(AI_POLICY_RE.search(cfp_html)),
    )

    output_path = pathlib.Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(md + "\n", encoding="utf-8")
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
