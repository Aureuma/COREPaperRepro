# MetaWorld Slice Statistical Summary (Auto-generated)

- Input: `output/corepaper_reports/ws3/metaworld_seedexp_adaptmanip_method_n30_results.json`
- Scenario: `shifted`
- Reference group: `method`

## Variant Summary

| Variant | N episodes | N seeds | Mean | Worst-seed mean | CVaR40 (seed) | Success/1k steps |
|---|---:|---:|---:|---:|---:|---:|
| adaptmanip | 300 | 30 | 0.5600 | 0.3000 | 0.4417 | 7.000 |
| method | 300 | 30 | 0.6967 | 0.5000 | 0.6333 | 8.708 |

## Reference Comparisons

| Comparison | N (ref/comp) | Ref Mean | Comp Mean | Delta Mean | Delta CI95 | Delta Worst-seed | Delta CVaR40(seed) | Cohen's d | p(mean) | p(CVaR40) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| method vs adaptmanip | 300/300 | 0.6967 | 0.5600 | +0.1367 | ±0.0767 | +0.2000 | +0.1917 | 0.285 | 0.000690 (monte_carlo) | 0.000000 (monte_carlo) |

## Compute Profile

- Total episodes (all scenarios): `600`
- Total episodes (shifted): `600`
- Training loop: `none (evaluation-only benchmark slice)`
- GPU-hours: `0.0`
