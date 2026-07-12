# MetaWorld Slice Statistical Summary (Auto-generated)

- Input: `output/corepaper_reports/ws3/metaworld_slice_results.json`
- Scenario: `shifted`
- Reference group: `method`

## Variant Summary

| Variant | N episodes | N seeds | Mean | Worst-seed mean | CVaR40 (seed) | Success/1k steps |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 50 | 5 | 0.1400 | 0.0000 | 0.0500 | 1.750 |
| ext1 | 50 | 5 | 0.2800 | 0.1000 | 0.2000 | 3.500 |
| ext2 | 50 | 5 | 0.4800 | 0.2000 | 0.2500 | 6.000 |
| method | 50 | 5 | 0.7000 | 0.6000 | 0.6500 | 8.750 |

## Reference Comparisons

| Comparison | N (ref/comp) | Ref Mean | Comp Mean | Delta Mean | Delta CI95 | Delta Worst-seed | Delta CVaR40(seed) | Cohen's d | p(mean) | p(CVaR40) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| method vs baseline | 50/50 | 0.7000 | 0.1400 | +0.5600 | ±0.1609 | +0.6000 | +0.6000 | 1.364 | 0.000000 (monte_carlo) | 0.007937 (exact) |
| method vs ext1 | 50/50 | 0.7000 | 0.2800 | +0.4200 | ±0.1796 | +0.5000 | +0.4500 | 0.917 | 0.000035 (monte_carlo) | 0.007937 (exact) |
| method vs ext2 | 50/50 | 0.7000 | 0.4800 | +0.2200 | ±0.1898 | +0.4000 | +0.4000 | 0.454 | 0.041200 (monte_carlo) | 0.126984 (exact) |

## Compute Profile

- Total episodes (all scenarios): `400`
- Total episodes (shifted): `200`
- Training loop: `none (evaluation-only benchmark slice)`
- GPU-hours: `0.0`
