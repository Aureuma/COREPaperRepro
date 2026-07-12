# Validity-Gap Status (Auto-generated)

- Inputs: `output/corepaper_reports/ws5/recent_paper_baselines.json` and `output/corepaper_reports/ws3/metaworld_recent_baselines_stats.json`
- Quality score: `4/5`

## Snapshot

- Stress aggregate top variant: `method` (margin vs #2: `0.0071`)
- MetaWorld shifted top variant: `method` (margin vs #2: `0.0200`)
- MetaWorld method-ext2 delta: `+0.2400`

## Flag Check

- `stress_top_is_method`: PASS
- `metaworld_top_is_method`: PASS
- `stress_margin_reasonable`: PASS
- `metaworld_margin_reasonable`: FAIL
- `metaworld_delta_vs_ext2_reasonable`: PASS

## Recommendations

- Expand recognized benchmark coverage (more tasks/seeds) to stabilize practical significance.
- Current direction is viable: lead with recognized benchmark, use scenario-model as mechanism evidence.
