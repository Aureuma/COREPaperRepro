# P-value Corrections (metaworld-shifted-recent)

- Input: `output/corepaper_reports/ws3/metaworld_recent_baselines_stats.json`
- Tests in family: `8`
- Alpha: `0.05`

| Comparison | p(raw) | p(Holm) | q(BH) | Sig(Holm) | Delta Mean | CI95 Excludes 0 | Cohen's d |
|---|---:|---:|---:|---|---:|---|---:|
| method vs baseline | 0.000000 | 0.000000 | 0.000000 | YES | +0.5800 | YES | 1.431 |
| method vs ext1 | 0.000025 | 0.000175 | 0.000100 | YES | +0.4200 | YES | 0.917 |
| method vs ext2 | 0.023890 | 0.119450 | 0.047780 | NO | +0.2400 | YES | 0.500 |
| method vs latency_aware | 1.000000 | 1.000000 | 1.000000 | NO | +0.0200 | NO | 0.044 |
| method vs adaptmanip | 0.396055 | 1.000000 | 0.528073 | NO | +0.1000 | NO | 0.212 |
| method vs robust_cp | 0.291915 | 1.000000 | 0.467064 | NO | +0.1200 | NO | 0.253 |
| method vs history_keyframe | 0.014145 | 0.084870 | 0.037720 | NO | +0.2600 | YES | 0.543 |
| method vs constrained_flow | 0.828305 | 1.000000 | 0.946634 | NO | +0.0400 | NO | 0.086 |

- Holm-significant comparisons: `2/8`
- BH-significant comparisons: `4/8`
