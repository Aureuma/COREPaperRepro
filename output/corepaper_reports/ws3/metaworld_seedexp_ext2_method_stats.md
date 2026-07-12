# MetaWorld Slice Statistical Summary (Auto-generated)

- Input: `output/corepaper_reports/ws3/metaworld_seedexp_ext2_method_results.json`
- Scenario: `shifted`
- Reference group: `method`

## Variant Summary

| Variant | N episodes | N seeds | Mean | Worst-seed mean | CVaR40 (seed) | Success/1k steps |
|---|---:|---:|---:|---:|---:|---:|
| ext2 | 140 | 14 | 0.4429 | 0.3000 | 0.3500 | 5.536 |
| method | 140 | 14 | 0.7071 | 0.5000 | 0.6167 | 8.839 |

## Reference Comparisons

| Comparison | N (ref/comp) | Ref Mean | Comp Mean | Delta Mean | Delta CI95 | Delta Worst-seed | Delta CVaR40(seed) | Cohen's d | p(mean) | p(CVaR40) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| method vs ext2 | 140/140 | 0.7071 | 0.4429 | +0.2643 | ±0.1120 | +0.2000 | +0.2667 | 0.553 | 0.000005 (monte_carlo) | 0.000010 (monte_carlo) |

## Compute Profile

- Total episodes (all scenarios): `280`
- Total episodes (shifted): `280`
- Training loop: `none (evaluation-only benchmark slice)`
- GPU-hours: `0.0`
