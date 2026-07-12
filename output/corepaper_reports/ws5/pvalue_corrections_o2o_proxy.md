# P-value Corrections (o2o-proxy-stress)

- Input: `output/corepaper_reports/ws5/o2o_proxy_recent.json`
- Tests in family: `5`
- Alpha: `0.05`

| Comparison | p(raw) | p(Holm) | q(BH) | Sig(Holm) | Delta Mean | CI95 Excludes 0 | Cohen's d |
|---|---:|---:|---:|---|---:|---|---:|
| method vs baseline | 0.000000 | 0.000000 | 0.000000 | YES | +0.0675 | YES | 3.449 |
| method vs ext2 | 0.000000 | 0.000000 | 0.000000 | YES | +0.0290 | YES | 1.610 |
| method vs latency_aware | 0.000000 | 0.000000 | 0.000000 | YES | +0.0311 | YES | 1.697 |
| method vs adaptmanip | 0.000000 | 0.000000 | 0.000000 | YES | +0.0192 | YES | 1.017 |
| method vs robust_cp | 0.000000 | 0.000000 | 0.000000 | YES | +0.0224 | YES | 1.271 |

- Holm-significant comparisons: `5/5`
- BH-significant comparisons: `5/5`
