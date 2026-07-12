# P-value Corrections (training-backed-stress)

- Input: `output/corepaper_reports/ws5/training_backed_recent.json`
- Tests in family: `5`
- Alpha: `0.05`

| Comparison | p(raw) | p(Holm) | q(BH) | Sig(Holm) | Delta Mean | CI95 Excludes 0 | Cohen's d |
|---|---:|---:|---:|---|---:|---|---:|
| method vs baseline | 0.000000 | 0.000000 | 0.000000 | YES | -0.2226 | YES | -3.267 |
| method vs ext2 | 0.000000 | 0.000000 | 0.000000 | YES | -0.2108 | YES | -3.062 |
| method vs latency_aware | 0.000000 | 0.000000 | 0.000000 | YES | -0.2056 | YES | -2.917 |
| method vs adaptmanip | 0.000000 | 0.000000 | 0.000000 | YES | -0.2183 | YES | -3.196 |
| method vs robust_cp | 0.000000 | 0.000000 | 0.000000 | YES | -0.2009 | YES | -2.833 |

- Holm-significant comparisons: `5/5`
- BH-significant comparisons: `5/5`
