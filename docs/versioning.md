# Versioning Policy

This repository uses a single release version for code, experiments, and paper artifacts.

## Canonical Version Fields

The canonical hard-coded version field is:

1. `VERSION`

`pyproject.toml` must derive package metadata from `VERSION` through
`tool.setuptools.dynamic.version.file = ["VERSION"]`.

Validation command:

```bash
uv run python scripts/version/check_version_sync.py
```

Automatic bump command:

```bash
uv run python scripts/version/bump_version.py --part patch
```

## Required Files Per Versioned Snapshot

Each version bump must be committed together with the corresponding regenerated artifacts, not code-only changes.

Minimum required artifact bundle:

1. `paper/generated/results_macros.tex`
2. `paper/build/manuscript.pdf`
3. `output/corepaper_reports/ws3/*.json` for MetaWorld summary + seed-expansion stats
4. `output/corepaper_reports/ws5/*.json` for statistical effects
5. `paper/figures/*` regenerated from current reports
6. `output/corepaper_reports/version_snapshot.json`
7. `CHANGELOG.md` updated for the bumped version with critique/plan/implementation notes

Snapshot generation command:

```bash
uv run python scripts/version/write_version_snapshot.py
```

## Version Bump Procedure

Primary path (recommended): let the pipeline bump automatically after a successful end-to-end run.

1. Run full pipeline with auto-bump:
   `uv run python scripts/paper/run_full_pipeline.py`
   - Critique mode is `counsel` only (multi-round Gemini<->Claude consensus loop).
   - Council provider calls are batch-only for cost control (`--batch-manifest` path).
   - Council implementation is inspired by Karpathy's `llm-council`: `https://github.com/karpathy/llm-council`.
2. Confirm version sync:
   `uv run python scripts/version/check_version_sync.py`
3. Update `CHANGELOG.md` for the new version using this required section order:
   - `Critique Feedback (Risk, Ratings, Reasoning)`
   - `Plan Changes`
   - `Implementation Changes`
4. Commit all related files together:
   code + configs + reports + macros + figures + PDF + version snapshot + changelog.

Manual path (when needed): explicit set or custom increment.

1. Run `uv run python scripts/version/bump_version.py --part patch` (or `minor`/`major`).
2. Run `uv run python scripts/paper/generate_result_macros.py`.
3. Run `uv run python scripts/version/write_version_snapshot.py`.
4. Run `uv lock` if dependency metadata changed.
5. Update `CHANGELOG.md` using the required section order and include critique risk/ratings/reasoning details.
6. Commit code + configs + outputs + changelog together.

Do not create a version bump commit that omits regenerated runs/results/macros.
