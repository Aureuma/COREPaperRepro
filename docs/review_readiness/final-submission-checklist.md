# Final Submission Checklist

Last updated: 2026-03-02

## Scope and Artifacts

- Manuscript source: `paper/manuscript.tex`
- Compiled PDF: `paper/build/manuscript.pdf`
- Sentence/concept traceability CSV: `docs/review_readiness/final_submission_sentence_map.csv`
- Cross-reference consistency CSV: `docs/review_readiness/final_submission_crossref_map.csv`
- Bibliography audit CSV: `docs/review_readiness/final_submission_bibliography_audit.csv`
- Page-edge/layout audit CSV: `docs/review_readiness/final_submission_layout_audit.csv`

## Build and Compliance Checks

- [x] PDF format and page budget fully compliant
- [x] PDF generated: `True`
- [x] PDF size under 6 MB: `376732` bytes
- [x] Page count detected: `8`
- [x] No undefined citations in log: `0`
- [x] No undefined refs in log: `0`
- [x] Overfull hbox count: `0`
- [ ] Underfull hbox count (review style only): `49`

```text
Title:           CORE: Uncertainty-Gated Policy Optimization for Reliable Performance Under Distribution Shift
Subject:         Double-anonymous review submission
Author:          Anonymous
Creator:         TeX
Producer:        pdfTeX-1.40.26
CreationDate:    Mon Mar  2 16:01:56 2026 UTC
ModDate:         Mon Mar  2 16:01:56 2026 UTC
Custom Metadata: no
Metadata Stream: no
Tagged:          no
UserProperties:  no
Suspects:        no
Form:            none
JavaScript:      no
Pages:           8
Encrypted:       no
Page size:       612 x 792 pts (letter)
Page rot:        0
File size:       376732 bytes
Optimized:       no
PDF version:     1.5
```

## Policy and Submission-Rule Check (Web-Verified on 2026-03-02)

| Policy topic | Source | What it says | Status for this repo |
|---|---|---|---|
| IEEE RAS anonymization rule | https://www.ieee-ras.org/publications/rules-for-the-double-anonymous-review-process/ | RAS provides double-anonymous guidance and redaction practices. | Current manuscript setup is aligned (`censor`, anonymized metadata). |
| IROS review model (target year CFP) | https://2026.ieee-iros.org/contribute/call-for-papers/ | CFP states double-anonymous workflow and references RAS review rules. | Resolved: keep manuscript in anonymized mode (`\\doubleanonymousreviewtrue`). |
| IROS 2026 deadlines source | https://2026.ieee-iros.org/about/important-dates/ | Official paper submission deadline is March 2, 2026; final paper deadline is July 10, 2026. | Confirmed via local WS0 snapshot. |
| PDF and template submission rules | https://2026.ieee-iros.org/contribute/call-for-papers/ | English PDF (up to 6 MB) via PaperPlaza; official LaTeX/Word templates linked. | Current build and file size satisfy these rules. |

Policy gate before upload: resolved on 2026-03-02 from official IROS 2026 CFP; submission mode remains double-anonymous.

## Sentence and Concept Mapping

| Section | Sentences mapped |
|---|---:|
| Abstract | 4 |
| Conclusion | 4 |
| Discussion and Limitations | 4 |
| Experiments | 45 |
| Introduction | 15 |
| Related Work | 7 |
| Theory and Design Rationale | 66 |

- Sentences flagged for review: **42**
- Notes:
  - `relevance=review` means sentence lacks clear section-expected concept tags or is unusually long.
  - Full sentence-level rows are in the CSV artifact above.

## Reference Numbering and Mention Consistency

- Cross-reference rows: **28**
- Missing label failures: **0**
- Defined-but-never-cited reviews: **0**

## Bibliography Style Audit

- Cited keys audited: **28**
- Missing-entry failures: **0**
- Missing-required-field reviews: **0**

## Page Geometry and Edge Audit

- Pages reviewed with bbox extraction: **8**
- Pages requiring manual review: **0**

| Page | Left (pt) | Right (pt) | Top (pt) | Bottom (pt) | Center-cross words | Status |
|---:|---:|---:|---:|---:|---:|---|
| 1 | 54.0 | 54.0 | 74.0 | 58.3 | 2 | pass |
| 2 | 54.0 | 54.0 | 50.1 | 56.3 | 0 | pass |
| 3 | 54.0 | 54.0 | 52.9 | 56.3 | 0 | pass |
| 4 | 54.0 | 54.0 | 52.0 | 57.0 | 0 | pass |
| 5 | 54.0 | 54.0 | 50.1 | 58.3 | 0 | pass |
| 6 | 54.0 | 54.0 | 50.1 | 58.3 | 0 | pass |
| 7 | 54.0 | 54.0 | 53.3 | 58.8 | 0 | pass |
| 8 | 54.0 | 313.2 | 56.6 | 638.6 | 0 | pass |

## Desk-Reject Risk Card (Automatable Checks)

| Item | Status | Evidence |
|---|---|---|
| Template/PDF build integrity | PASS | `pdfinfo` + generated PDF present |
| Citation/reference integrity | PASS | LaTeX log undefined counts |
| Equation/table/figure numbering linkage | PASS | Cross-reference CSV |
| Margin/edge overflow | PASS | Layout CSV |
| Overfull text overflow | PASS | LaTeX log overfull count |
| Anonymization metadata | PASS (current PDF) | `pdfinfo` Author=Anonymous, Subject set |
| Policy-model alignment (single-blind vs double-anonymous) | PASS | Official IROS 2026 CFP requires double-anonymous workflow; manuscript toggle kept on. |
