# MetaWorld Slice Statistical Summary (Auto-generated)

- Input: `output/corepaper_reports/ws3/metaworld_seedexp_latency_method_results.json`
- Scenario: `shifted`
- Reference group: `method`

## Variant Summary

| Variant | N episodes | N seeds | Mean | Worst-seed mean | CVaR40 (seed) | Success/1k steps |
|---|---:|---:|---:|---:|---:|---:|
| latency_aware | 140 | 14 | 0.6429 | 0.4000 | 0.5500 | 8.036 |
| method | 140 | 14 | 0.7286 | 0.6000 | 0.6500 | 9.107 |

## Reference Comparisons

| Comparison | N (ref/comp) | Ref Mean | Comp Mean | Delta Mean | Delta CI95 | Delta Worst-seed | Delta CVaR40(seed) | Cohen's d | p(mean) | p(CVaR40) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| method vs latency_aware | 140/140 | 0.7286 | 0.6429 | +0.0857 | ±0.1087 | +0.2000 | +0.1000 | 0.185 | 0.155620 (monte_carlo) | 0.118345 (monte_carlo) |

## Compute Profile

- Total episodes (all scenarios): `280`
- Total episodes (shifted): `280`
- Training loop: `none (evaluation-only benchmark slice)`
- GPU-hours: `0.0`
