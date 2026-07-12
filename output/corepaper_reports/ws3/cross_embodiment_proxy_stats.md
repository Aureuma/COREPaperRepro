# Cross-Embodiment Transfer Statistical Summary (Auto-generated)

- Input: `output/corepaper_reports/ws3/cross_embodiment_proxy_results.json`
- Scenario: `shifted`
- Source embodiment: `franka`
- Reference group: `method`

## Variant Summary

| Variant | N episodes | N seeds | N targets | Mean | Worst-seed mean | CVaR40(seed) | Success/1k steps |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline | 144 | 8 | 3 | 0.3692 | 0.3672 | 0.3681 | 4.040 |
| ext1 | 144 | 8 | 3 | 0.3992 | 0.3956 | 0.3970 | 4.346 |
| ext2 | 144 | 8 | 3 | 0.4277 | 0.4243 | 0.4252 | 4.651 |
| latency_aware | 144 | 8 | 3 | 0.4333 | 0.4283 | 0.4311 | 4.716 |
| adaptmanip | 144 | 8 | 3 | 0.4331 | 0.4255 | 0.4298 | 4.711 |
| robust_cp | 144 | 8 | 3 | 0.4322 | 0.4285 | 0.4303 | 4.719 |
| method | 144 | 8 | 3 | 0.4621 | 0.4594 | 0.4601 | 5.045 |

## Reference Comparisons

| Comparison | N (ref/comp) | Delta Mean | Delta CI95 | Delta Worst-seed | Delta CVaR40(seed) | Cohen's d | p-value |
|---|---:|---:|---:|---:|---:|---:|---:|
| method vs baseline | 144/144 | +0.0929 | ±0.0057 | +0.0923 | +0.0921 | 3.753 | 0.000000 |
| method vs ext1 | 144/144 | +0.0629 | ±0.0058 | +0.0638 | +0.0631 | 2.504 | 0.000000 |
| method vs ext2 | 144/144 | +0.0343 | ±0.0058 | +0.0351 | +0.0350 | 1.369 | 0.000000 |
| method vs latency_aware | 144/144 | +0.0288 | ±0.0056 | +0.0312 | +0.0291 | 1.182 | 0.000000 |
| method vs adaptmanip | 144/144 | +0.0289 | ±0.0057 | +0.0340 | +0.0303 | 1.167 | 0.000000 |
| method vs robust_cp | 144/144 | +0.0299 | ±0.0057 | +0.0309 | +0.0298 | 1.215 | 0.000000 |
