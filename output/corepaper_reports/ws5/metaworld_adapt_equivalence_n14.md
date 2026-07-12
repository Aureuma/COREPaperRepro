# Adaptmanip N=14 Equivalence Audit (Auto-generated)

- Input: `output/corepaper_reports/ws3/metaworld_seedexp_adaptmanip_method_results.json`
- Scenario: `shifted`
- Variants: `method` vs `adaptmanip`
- Shared seeds: 14
- Equivalence margin: ±0.0500
- Bootstrap samples: 10000

| Metric | Observed delta | 90% CI | 95% CI | P(delta<=-margin) | P(delta>=+margin) | Equivalence supported |
|---|---:|---:|---:|---:|---:|---:|
| mean_seed_success | +0.0786 | [+0.0357, +0.1214] | [+0.0286, +0.1357] | 0.0000 | 0.8561 | no |
| cvar40_seed_success | +0.1333 | [+0.0500, +0.2000] | [+0.0333, +0.2167] | 0.0000 | 0.9507 | no |

- Mean equivalence supported: no
- CVaR equivalence supported: no

Equivalence is only supported when the 90% bootstrap CI lies fully inside [-margin, +margin] for the target metric.
