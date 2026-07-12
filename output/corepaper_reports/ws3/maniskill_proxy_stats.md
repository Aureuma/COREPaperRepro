# MetaWorld Slice Statistical Summary (Auto-generated)

- Input: `output/corepaper_reports/ws3/maniskill_proxy_results.json`
- Scenario: `shifted`
- Reference group: `method`

## Variant Summary

| Variant | N episodes | N seeds | Mean | Worst-seed mean | CVaR40 (seed) | Success/1k steps |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 64 | 8 | 0.3226 | 0.3200 | 0.3208 | 3.718 |
| ext1 | 64 | 8 | 0.3639 | 0.3596 | 0.3605 | 4.183 |
| ext2 | 64 | 8 | 0.3946 | 0.3893 | 0.3912 | 4.522 |
| latency_aware | 64 | 8 | 0.4002 | 0.3881 | 0.3953 | 4.609 |
| adaptmanip | 64 | 8 | 0.4026 | 0.3989 | 0.4000 | 4.644 |
| robust_cp | 64 | 8 | 0.4025 | 0.3962 | 0.3977 | 4.606 |
| method | 64 | 8 | 0.4277 | 0.4216 | 0.4243 | 4.935 |

## Reference Comparisons

| Comparison | N (ref/comp) | Ref Mean | Comp Mean | Delta Mean | Delta CI95 | Delta Worst-seed | Delta CVaR40(seed) | Cohen's d | p(mean) | p(CVaR40) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| method vs baseline | 64/64 | 0.4277 | 0.3226 | +0.1050 | ±0.0090 | +0.1016 | +0.1034 | 4.049 | 0.000000 (monte_carlo) | 0.000155 (exact) |
| method vs ext1 | 64/64 | 0.4277 | 0.3639 | +0.0638 | ±0.0094 | +0.0620 | +0.0638 | 2.351 | 0.000000 (monte_carlo) | 0.000155 (exact) |
| method vs ext2 | 64/64 | 0.4277 | 0.3946 | +0.0331 | ±0.0093 | +0.0323 | +0.0331 | 1.233 | 0.000000 (monte_carlo) | 0.000155 (exact) |
| method vs latency_aware | 64/64 | 0.4277 | 0.4002 | +0.0275 | ±0.0096 | +0.0335 | +0.0290 | 0.989 | 0.000000 (monte_carlo) | 0.000155 (exact) |
| method vs adaptmanip | 64/64 | 0.4277 | 0.4026 | +0.0251 | ±0.0094 | +0.0227 | +0.0243 | 0.920 | 0.000000 (monte_carlo) | 0.000155 (exact) |
| method vs robust_cp | 64/64 | 0.4277 | 0.4025 | +0.0252 | ±0.0092 | +0.0253 | +0.0266 | 0.951 | 0.000000 (monte_carlo) | 0.000155 (exact) |

## Compute Profile

- Total episodes (all scenarios): `896`
- Total episodes (shifted): `448`
- Training loop: `none (evaluation-only benchmark slice)`
- GPU-hours: `0.0`
