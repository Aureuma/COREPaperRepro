# MetaWorld Slice Statistical Summary (Auto-generated)

- Input: `output/corepaper_reports/ws3/metaworld_seedexp_latency_method_n30_results.json`
- Scenario: `shifted`
- Reference group: `method`

## Variant Summary

| Variant | N episodes | N seeds | Mean | Worst-seed mean | CVaR40 (seed) | Success/1k steps |
|---|---:|---:|---:|---:|---:|---:|
| latency_aware | 300 | 30 | 0.6600 | 0.5000 | 0.5667 | 8.250 |
| method | 300 | 30 | 0.7133 | 0.5000 | 0.6167 | 8.917 |

## Reference Comparisons

| Comparison | N (ref/comp) | Ref Mean | Comp Mean | Delta Mean | Delta CI95 | Delta Worst-seed | Delta CVaR40(seed) | Cohen's d | p(mean) | p(CVaR40) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| method vs latency_aware | 300/300 | 0.7133 | 0.6600 | +0.0533 | ±0.0742 | +0.0000 | +0.0500 | 0.115 | 0.187500 (monte_carlo) | 0.352280 (monte_carlo) |

## Compute Profile

- Total episodes (all scenarios): `600`
- Total episodes (shifted): `600`
- Training loop: `none (evaluation-only benchmark slice)`
- GPU-hours: `0.0`
