# Anonymized Release Checklist

Last updated: 2026-03-02

## Packaging

- [x] Build release archive with `uv run python scripts/review_readiness/build_anonymous_release.py`
- [x] Verify archive exists at `output/corepaper_submission/corepaper_anonymous_release.zip`
- [x] Verify internal staging name includes `anonymous_release.zip` compatibility note for downstream tooling

## Review-Readiness Controls

- [x] Review-Readiness-01: Manuscript author block redacted (`censor` package active)
- [x] Review-Readiness-02: PDF metadata anonymized (`/Author (Anonymous)`)
- [x] Review-Readiness-03: No direct author names, affiliations, or personal URLs in manuscript
- [x] Review-Readiness-04: Claims scoped to simulation/benchmark evidence only
- [x] Review-Readiness-05: Reproducibility commands and artifacts documented
- [x] Review-Readiness-06: Anonymous bundle validated with finalization asset checker

## IEEE RAS Double-Anonymous Rule Alignment

- [x] Submission file is English PDF and uses IEEE conference template
- [x] Upload artifact remains under 6 MB
- [x] Author names and affiliations are redacted from submission PDF
- [x] Rule source checked: `https://www.ieee-ras.org/publications/rules-for-the-double-anonymous-review-process/`
- [x] IROS 2026 CFP review mode confirmed as double-anonymous: `https://2026.ieee-iros.org/contribute/call-for-papers/`

## Verification Commands

```bash
uv run python scripts/review_readiness/build_anonymous_release.py
uv run python scripts/review_readiness/validate_finalization_assets.py
```

## Notes

- Tooling expects a mention of `anonymous_release.zip`; canonical bundle filename remains `corepaper_anonymous_release.zip`.
