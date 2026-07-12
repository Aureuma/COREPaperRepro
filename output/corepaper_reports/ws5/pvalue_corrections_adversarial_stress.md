# P-value Corrections (adversarial-composed-shifts)

- Input: `output/corepaper_reports/ws5/adversarial_stress_results.json`
- Tests in family: `5`
- Alpha: `0.05`

| Comparison | p(raw) | p(Holm) | q(BH) | Sig(Holm) | Delta Mean | CI95 Excludes 0 | Cohen's d |
|---|---:|---:|---:|---|---:|---|---:|
| method vs baseline | 0.000000 | 0.000000 | 0.000000 | YES | +0.0931 | YES | 5.642 |
| method vs ext2 | 0.000000 | 0.000000 | 0.000000 | YES | +0.0356 | YES | 2.324 |
| method vs latency_aware | 0.000000 | 0.000000 | 0.000000 | YES | +0.0326 | YES | 2.040 |
| method vs adaptmanip | 0.000000 | 0.000000 | 0.000000 | YES | +0.0308 | YES | 1.995 |
| method vs robust_cp | 0.000000 | 0.000000 | 0.000000 | YES | +0.0256 | YES | 1.729 |

- Holm-significant comparisons: `5/5`
- BH-significant comparisons: `5/5`
