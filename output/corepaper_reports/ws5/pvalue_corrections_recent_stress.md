# P-value Corrections (recent-stress)

- Input: `output/corepaper_reports/ws5/recent_paper_baselines.json`
- Tests in family: `8`
- Alpha: `0.05`

| Comparison | p(raw) | p(Holm) | q(BH) | Sig(Holm) | Delta Mean | CI95 Excludes 0 | Cohen's d |
|---|---:|---:|---:|---|---:|---|---:|
| method vs baseline | 0.000000 | 0.000000 | 0.000000 | YES | +0.0534 | YES | 2.015 |
| method vs ext1 | 0.000000 | 0.000000 | 0.000000 | YES | +0.0278 | YES | 1.094 |
| method vs ext2 | 0.011265 | 0.056325 | 0.018328 | NO | +0.0109 | YES | 0.436 |
| method vs latency_aware | 0.075770 | 0.151540 | 0.086594 | NO | +0.0078 | NO | 0.303 |
| method vs adaptmanip | 0.100505 | 0.151540 | 0.100505 | NO | +0.0071 | NO | 0.280 |
| method vs robust_cp | 0.003345 | 0.020070 | 0.008920 | YES | +0.0126 | YES | 0.510 |
| method vs history_keyframe | 0.011455 | 0.056325 | 0.018328 | NO | +0.0117 | YES | 0.436 |
| method vs constrained_flow | 0.020940 | 0.062820 | 0.027920 | NO | +0.0094 | YES | 0.396 |

- Holm-significant comparisons: `3/8`
- BH-significant comparisons: `6/8`
