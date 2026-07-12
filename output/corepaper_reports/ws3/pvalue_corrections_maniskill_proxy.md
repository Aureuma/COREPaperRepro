# P-value Corrections (maniskill-proxy-shifted)

- Input: `output/corepaper_reports/ws3/maniskill_proxy_stats.json`
- Tests in family: `6`
- Alpha: `0.05`

| Comparison | p(raw) | p(Holm) | q(BH) | Sig(Holm) | Delta Mean | CI95 Excludes 0 | Cohen's d |
|---|---:|---:|---:|---|---:|---|---:|
| method vs baseline | 0.000000 | 0.000000 | 0.000000 | YES | +0.1050 | YES | 4.049 |
| method vs ext1 | 0.000000 | 0.000000 | 0.000000 | YES | +0.0638 | YES | 2.351 |
| method vs ext2 | 0.000000 | 0.000000 | 0.000000 | YES | +0.0331 | YES | 1.233 |
| method vs latency_aware | 0.000000 | 0.000000 | 0.000000 | YES | +0.0275 | YES | 0.989 |
| method vs adaptmanip | 0.000000 | 0.000000 | 0.000000 | YES | +0.0251 | YES | 0.920 |
| method vs robust_cp | 0.000000 | 0.000000 | 0.000000 | YES | +0.0252 | YES | 0.951 |

- Holm-significant comparisons: `6/6`
- BH-significant comparisons: `6/6`
