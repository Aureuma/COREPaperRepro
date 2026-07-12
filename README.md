# COREPaperRepro

COREPaperRepro contains the reproducibility package for CORE Paper. It includes the paper source, generated result macros, benchmark configuration files, analysis scripts, selected generated reports, and submission-facing artifacts needed to inspect and rerun the reported evidence.

Source snapshot:

- Source repository: `git@github.com:SHi-ON/COREPaper.git`
- Source commit: `bb50a535f6c5bd50fd2330aceaf6561a6473e18b`
- Package version: `0.3.6`

## Contents

- `paper/`: LaTeX source, generated macros, figures, and the compiled manuscript snapshot at `paper/build/manuscript.pdf`.
- `config/`: benchmark manifests and run configuration.
- `scripts/`: validation, analysis, figure, paper, and packaging scripts.
- `output/corepaper_reports/experiments/`: smoke experiment summaries and integrity reports.
- `output/corepaper_reports/ws3/`: main benchmark and baseline comparison reports.
- `output/corepaper_reports/ws5/`: statistical, robustness, ablation, parity, and sensitivity reports.
- `output/corepaper_submission/`: submission-facing PDF, metadata, checksums, notes, and video artifact.

## Quick Start

Install dependencies:

```bash
uv sync
```

Run lightweight validation checks:

```bash
uv run python scripts/version/check_version_sync.py
uv run python -m unittest tests/test_version_bump.py
uv run python scripts/experiments/validate_experiment_stack.py
uv run python scripts/figures/validate_figures.py
```

Regenerate manuscript result macros from the included reports:

```bash
uv run python scripts/paper/generate_result_macros.py
```

Build the manuscript PDF with the repository's Docker-based TeX path:

```bash
uv run python scripts/paper/build_iros2026_pdf_docker.py
```

The original final-submission sanity checker is included for provenance, but it contains double-anonymous submission gates from the source workflow. The public reproducibility checks above validate the included source, reports, figures, and version metadata without requiring anonymous-review redaction state.

Some experiment reruns require optional simulator dependencies. For MetaWorld-dependent tasks:

```bash
uv sync --extra metaworld
uv run corepaper experiments-cycle
```

## License

This work is licensed under a Creative Commons Attribution 4.0 International License (CC BY 4.0). See `LICENSE`.
