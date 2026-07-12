# CORE Paper Visual Identity and Media Pipeline (IROS 2026)

## Purpose
This file defines one consistent visual system for all CORE Paper artifacts:
- manuscript figures
- tables and plot styling
- supplementary video assets
- generated overlays used in automated media scripts

This is the single reference for humans and code agents when creating visuals.

## Venue Context (IEEE / IROS 2026)
- Venue target: IEEE/RSJ IROS 2026.
- Paper format: IEEE conference template conventions (double-column, high-density technical visuals).
- Initial paper deadline: March 2, 2026.
- Paper-video deadline shown on official IROS 2026 pages: March 5, 2026.
- IROS CFP text indicates a 1-minute video supplement can be attached (MPG/MPEG/MP4, up to 10 MB).

Source pages:
- https://2026.ieee-iros.org/about/important-dates/
- https://2026.ieee-iros.org/contribute/call-for-papers/

## Canonical Style Tokens
Machine-readable source of truth:
- `config/visual_identity.json`

### Color Palette (semantic roles)
- `ink_primary`: `#0F172A` (headlines, axes, titles)
- `ink_secondary`: `#334155` (secondary labels)
- `bg_canvas`: `#F4F7FB` (canvas/background)
- `bg_panel`: `#E6EDF7` (panel/card background)
- `grid`: `#CBD5E1` (gridlines)
- `baseline`: `#6E8EA9`
- `reference_a`: `#8BBC6E`
- `reference_b`: `#E2A75D`
- `reference_c`: `#6B8FD6` (latency-aware reference)
- `reference_d`: `#4FA89A` (adaptation reference)
- `reference_e`: `#9A7FD1` (conformal-safe reference)
- `method`: `#D94B4B`
- `success`: `#2E9E62`
- `warning`: `#D97706`

### Typography
- Manuscript body: IEEE template default (Times family via `ieeeconf.cls`).
- Generated figures and video overlays: DejaVu Sans family for deterministic rendering.
- Video font files:
  - `/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf`
  - `/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf`

## Figure System (Paper Visuals)
Use these defaults unless a specific figure requires deviation:
- Base export size: `960x540` (16:9) for external assets.
- Axis line thickness: `2 px`.
- Font sizes:
  - title: `22 px`
  - axis/category labels: `12 px`
  - numeric value annotations: `13 px`
- Method color must always be `#D94B4B`.
- Baseline and reference colors must remain stable across all plots.
- Y-axes start at zero for bar charts unless explicitly justified.
- Include direct numeric labels for main comparison bars.

### Python Visualization Packages
Recommended for new figure development:
1. `matplotlib` for publication plots (static, deterministic export).
2. `seaborn` for style wrappers over `matplotlib` (when helpful).
3. `numpy` / `pandas` for data shaping.
4. `scipy` for statistical overlays/tests.

Repository fallback path (no external plotting stack required):
- `scripts/figures/generate_paper_figures.py`
- `scripts/figures/export_png_figures.py`

## Video Identity (Supplementary Media)
### Output spec
- Master format: MP4, H.264, `1280x720`, `30 fps`.
- Target supplement constraints: keep final clip around 1 minute and under 10 MB when required by portal constraints.

### Layout rules
- Use a neutral canvas (`bg_canvas`) and a bordered panel for clip content.
- Top title bar:
  - paper/method label
  - scenario label
- Bottom information bar:
  - baseline score
  - method score
  - delta (method - baseline)
- Add legend chips with canonical baseline/method colors.
- Keep overlays readable in compressed video:
  - title >= 40 px
  - subtitle/body >= 22 px

### Timing rules
- Intro card: `2.5 s`.
- Each scenario segment: `4.0 s`.
- Outro card: `2.0 s`.
- Scenario order default:
  1. `S1-hard`
  2. `S2-med`
  3. `S3-severe`
  4. `SIM-isaac`

## Reproducible Video Pipeline
Primary entrypoint:
- `scripts/vis/build_video_pipeline.py`
- Dependency: local `ffmpeg` on `PATH` or Docker fallback (`lscr.io/linuxserver/ffmpeg:latest`).

Pipeline stages:
1. Generate deterministic base clips and metrics manifest:
   - `python3 scripts/vis/render_video.py ...`
2. Build polished, branded MP4 segments + concatenated final cut:
   - `python3 scripts/vis/polish_video.py ...`
3. Export submission assets:
   - `output/corepaper_submission/corepaper_video.mp4`

### Standard command
```bash
python3 scripts/vis/build_video_pipeline.py
```

### Generated outputs
- `output/corepaper_assets/video/manifest.json` (base clip metadata)
- `output/corepaper_assets/video/corepaper_video_pipeline_manifest.json` (polished pipeline metadata)
- `output/corepaper_assets/video/corepaper_video_polished.mp4`
- `output/corepaper_submission/corepaper_video.mp4`

## Agent Rules (must-follow)
When any agent generates a new figure/video:
1. Read `config/visual_identity.json`.
2. Use canonical method/baseline/reference colors exactly.
3. Use DejaVu Sans for generated overlays unless explicitly overridden.
4. Keep naming under `output/` with `corepaper_` prefix for top-level generated artifacts.
5. Do not introduce ad-hoc palettes or random font stacks.
6. If a figure intentionally deviates, document the reason in the PR/commit message.
