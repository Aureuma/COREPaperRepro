# P-value Corrections (library-lane-stress)

- Input: `output/corepaper_reports/ws5/library_lane.json`
- Tests in family: `2`
- Alpha: `0.05`

| Comparison | p(raw) | p(Holm) | q(BH) | Sig(Holm) | Delta Mean | CI95 Excludes 0 | Cohen's d |
|---|---:|---:|---:|---|---:|---|---:|
| method vs sb3_ppo | 0.000025 | 0.000050 | 0.000050 | YES | +0.0220 | YES | 0.902 |
| method vs rllib_sac | 0.000990 | 0.000990 | 0.000990 | YES | +0.0160 | YES | 0.677 |

- Holm-significant comparisons: `2/2`
- BH-significant comparisons: `2/2`
