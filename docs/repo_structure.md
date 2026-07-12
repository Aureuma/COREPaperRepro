# Repository Structure Rules (Template)

## Scope
- This file is the default structure template for paper repositories that combine code, experiments, and LaTeX.
- Keep it generic enough to reuse in future paper repos with only naming-prefix changes.

## Directory Roles
- `paper/`: LaTeX source only (`manuscript.tex` as the canonical manuscript, `.bib`, style/class files, `figures/`, `generated/`).
- `paper/build/`: TeX build outputs only (PDF, aux, bbl, logs).
- `scripts/`: all automation (experiments, analysis, figures, tables/macros, validation, packaging).
- `config/`: explicit run/configuration inputs; no generated outputs.
- `data/`: source datasets, ingested paper metadata, caches, and intermediate parsing inputs.
- `output/`: generated artifacts only (logs, reports, media, bundles).
- `docs/`: process docs and authoring guides (`plan.md`, visual identity, notation guide, this file).
- `tickets/`: local scratch notes and task reminders (git-ignored by default; keep only a tracked template note if needed).

## Output Layout
- `output/<repo_prefix>_reports/`: markdown/json reports and derived metrics.
- `output/<repo_prefix>_logs/`: execution logs, run traces, seed-level artifacts.
- `output/<repo_prefix>_assets/`: generated figures/media previews.
- `output/<repo_prefix>_submission/`: bundles and release zips.

## Naming and Path Rules
- Use a single repo prefix for generated outputs (here: `corepaper_`).
- Never write generated files to repo root, `docs/`, or `config/`.
- Keep final manuscript build files under `paper/build/` only.
- Keep paper-ready figure files under `paper/figures/` in vector formats (`.pdf` preferred).
- Keep machine-generated manuscript numbers in `paper/generated/results_macros.tex`.

## Reproducibility Rules
- One command must regenerate all paper artifacts end-to-end.
- Validation must run after generation and fail on missing required artifacts.
- Pin toolchain through `uv` (`pyproject.toml` + `uv.lock`) and containerized TeX when applicable.
- Preserve seeds and configuration snapshots in `output/<repo_prefix>_logs/`.

## Manuscript Number Policy
- Do not hardcode result numbers in LaTeX text, tables, captions, abstract, or conclusions.
- Generate all numeric claims from scripts into LaTeX macros, then `\input{paper/generated/results_macros.tex}`.
- If a number appears in prose, it must map to a macro key.

## Figure Policy
- Prefer information-dense figures that combine related signals when page budget is constrained.
- Maintain a single visual identity (colors, fonts, line widths, spacing) across all plots.
- Export publication figures as vector assets for `paper/figures/`; raster previews go to `output/<repo_prefix>_assets/`.

## Secrets and Credentials
- Never store plaintext credentials in repo files.
- Use SI Vault (or equivalent secure runtime injection) for API keys and cloud credentials.
- Scripts must read credentials from environment variables populated at runtime.

## Code Release Split (Paper vs Public Code Repo)
- Keep this repo focused on paper execution and artifact generation.
- Prepare a separate public code release repo near submission/camera-ready, after results are stable.
- Public release checklist:
- remove private/internal notes and credentials hooks;
- include reproducible run instructions and pinned dependencies;
- include license, citation metadata, and minimal benchmark assets;
- include a script to regenerate reported tables/figures from released inputs.

## Generic Examples
- Good: `output/corepaper_submission/corepaper_submission_bundle.zip`
- Good: `output/corepaper_reports/ws5/statistical_effects.json`
- Good: `paper/figures/metaworld_taskwise.pdf`
- Bad: `reports/ws5/statistical_effects.json`
- Bad: `paper/main.pdf` (use `paper/build/manuscript.pdf`)
