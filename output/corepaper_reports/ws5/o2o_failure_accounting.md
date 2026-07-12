# Offline-to-Online Failure Accounting (Auto-generated)

- Logs dir: `output/corepaper_logs/experiments/o2o_proxy_latest`
- Reference group: `method`

## Variant Summary

| Variant | N | Mean Offline | Mean Online | Mean Gain | Mean Interventions | Mean Catastrophic Events |
|---|---:|---:|---:|---:|---:|---:|
| baseline | 60 | 0.6095 | 0.6341 | +0.0246 | 2.90 | 0.27 |
| ext2 | 60 | 0.6443 | 0.6716 | +0.0273 | 3.08 | 0.37 |
| latency_aware | 60 | 0.6437 | 0.6698 | +0.0261 | 3.17 | 0.33 |
| adaptmanip | 60 | 0.6501 | 0.6818 | +0.0317 | 3.10 | 0.37 |
| robust_cp | 60 | 0.6481 | 0.6779 | +0.0298 | 3.20 | 0.43 |
| method | 60 | 0.6618 | 0.6998 | +0.0380 | 3.57 | 0.27 |

## Reference Comparisons

| Comparison | Delta Online | Delta Gain | Delta Interventions | Delta Catastrophic Events |
|---|---:|---:|---:|---:|
| method vs baseline | +0.0657 | +0.0134 | +0.67 | +0.00 |
| method vs ext2 | +0.0283 | +0.0107 | +0.48 | -0.10 |
| method vs latency_aware | +0.0301 | +0.0119 | +0.40 | -0.07 |
| method vs adaptmanip | +0.0181 | +0.0063 | +0.47 | -0.10 |
| method vs robust_cp | +0.0220 | +0.0082 | +0.37 | -0.17 |
