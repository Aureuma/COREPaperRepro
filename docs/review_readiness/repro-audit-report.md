# Reproducibility Audit Report

Last updated: 2026-03-01

## Fresh-Clone Reproduction Results

The following commands are the baseline checks used in this workspace before finalization:

| Artifact | Command |
|---|---|
| Macro regeneration | `uv run python scripts/paper/generate_result_macros.py` |
| PDF build | `uv run python scripts/paper/build_iros2026_pdf_docker.py` |
| Pipeline sanity checks | `uv run python scripts/paper/pipeline_sanity_checks.py --label finalization-audit` |
| Version synchronization | `uv run python scripts/version/check_version_sync.py` |
| Anonymous release bundle | `uv run python scripts/review_readiness/build_anonymous_release.py` |
| Finalization asset validation | `uv run python scripts/review_readiness/validate_finalization_assets.py` |

## Expected Outputs

- `paper/build/manuscript.pdf`
- `paper/generated/results_macros.tex`
- `output/corepaper_submission/corepaper_anonymous_release.zip`
- `output/corepaper_reports/version_snapshot.json`

## Audit Notes

- Manuscript claims remain macro-backed; no hand-entered p-values in narrative claims.
- Author metadata is defined in `paper/manuscript.tex`.
- Scope claims remain simulation-only and explicitly avoid deployment guarantees.
