# MetaWorld Slice Statistical Summary (Auto-generated)

- Input: `output/corepaper_reports/ws3/metaworld_seedexp_adaptmanip_method_results.json`
- Scenario: `shifted`
- Reference group: `method`

## Variant Summary

| Variant | N episodes | N seeds | Mean | Worst-seed mean | CVaR40 (seed) | Success/1k steps |
|---|---:|---:|---:|---:|---:|---:|
| adaptmanip | 140 | 14 | 0.6214 | 0.4000 | 0.5167 | 7.768 |
| method | 140 | 14 | 0.7000 | 0.6000 | 0.6500 | 8.750 |

## Reference Comparisons

| Comparison | N (ref/comp) | Ref Mean | Comp Mean | Delta Mean | Delta CI95 | Delta Worst-seed | Delta CVaR40(seed) | Cohen's d | p(mean) | p(CVaR40) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| method vs adaptmanip | 140/140 | 0.7000 | 0.6214 | +0.0786 | ±0.1109 | +0.2000 | +0.1333 | 0.166 | 0.206820 (monte_carlo) | 0.049000 (monte_carlo) |

## Compute Profile

- Total episodes (all scenarios): `280`
- Total episodes (shifted): `280`
- Training loop: `none (evaluation-only benchmark slice)`
- GPU-hours: `0.0`
