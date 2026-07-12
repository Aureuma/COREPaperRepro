# MetaWorld Slice Statistical Summary (Auto-generated)

- Input: `output/corepaper_reports/ws3/metaworld_recent_baselines_results.json`
- Scenario: `shifted`
- Reference group: `method`

## Variant Summary

| Variant | N episodes | N seeds | Mean | Worst-seed mean | CVaR40 (seed) | Success/1k steps |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 50 | 5 | 0.1400 | 0.0000 | 0.0500 | 1.750 |
| ext1 | 50 | 5 | 0.3000 | 0.2000 | 0.2500 | 3.750 |
| ext2 | 50 | 5 | 0.4800 | 0.3000 | 0.4000 | 6.000 |
| latency_aware | 50 | 5 | 0.7000 | 0.6000 | 0.6500 | 8.750 |
| adaptmanip | 50 | 5 | 0.6200 | 0.5000 | 0.5500 | 7.750 |
| robust_cp | 50 | 5 | 0.6000 | 0.4000 | 0.5000 | 7.500 |
| history_keyframe | 50 | 5 | 0.4600 | 0.1000 | 0.2500 | 5.750 |
| constrained_flow | 50 | 5 | 0.6800 | 0.6000 | 0.6500 | 8.500 |
| method | 50 | 5 | 0.7200 | 0.6000 | 0.6500 | 9.000 |

## Reference Comparisons

| Comparison | N (ref/comp) | Ref Mean | Comp Mean | Delta Mean | Delta CI95 | Delta Worst-seed | Delta CVaR40(seed) | Cohen's d | p(mean) | p(CVaR40) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| method vs baseline | 50/50 | 0.7200 | 0.1400 | +0.5800 | ±0.1589 | +0.6000 | +0.6000 | 1.431 | 0.000000 (monte_carlo) | 0.007937 (exact) |
| method vs ext1 | 50/50 | 0.7200 | 0.3000 | +0.4200 | ±0.1796 | +0.4000 | +0.4000 | 0.917 | 0.000025 (monte_carlo) | 0.007937 (exact) |
| method vs ext2 | 50/50 | 0.7200 | 0.4800 | +0.2400 | ±0.1881 | +0.3000 | +0.2500 | 0.500 | 0.023890 (monte_carlo) | 0.015873 (exact) |
| method vs latency_aware | 50/50 | 0.7200 | 0.7000 | +0.0200 | ±0.1796 | +0.0000 | +0.0000 | 0.044 | 1.000000 (monte_carlo) | 1.000000 (exact) |
| method vs adaptmanip | 50/50 | 0.7200 | 0.6200 | +0.1000 | ±0.1851 | +0.1000 | +0.1000 | 0.212 | 0.396055 (monte_carlo) | 0.404762 (exact) |
| method vs robust_cp | 50/50 | 0.7200 | 0.6000 | +0.1200 | ±0.1861 | +0.2000 | +0.1500 | 0.253 | 0.291915 (monte_carlo) | 0.166667 (exact) |
| method vs history_keyframe | 50/50 | 0.7200 | 0.4600 | +0.2600 | ±0.1878 | +0.5000 | +0.4000 | 0.543 | 0.014145 (monte_carlo) | 0.087302 (exact) |
| method vs constrained_flow | 50/50 | 0.7200 | 0.6800 | +0.0400 | ±0.1813 | +0.0000 | +0.0000 | 0.086 | 0.828305 (monte_carlo) | 1.000000 (exact) |

## Compute Profile

- Total episodes (all scenarios): `900`
- Total episodes (shifted): `450`
- Training loop: `none (evaluation-only benchmark slice)`
- GPU-hours: `0.0`
