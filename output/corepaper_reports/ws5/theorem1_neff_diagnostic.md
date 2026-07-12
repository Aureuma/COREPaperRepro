# Theorem-1 Effective Sample Size Diagnostic (Auto-generated)

- Reference variant: `method`
- Scenario: `shifted`
- Min n_eff estimate: 300.0
- Conservative floor(min n_eff): 300
- Max seed-cluster ICC: 0.000

| Suite | Comparator | Paired rows | Seeds | Mean tasks/seed | ICC(seed) | Design effect | n_eff |
|---|---|---:|---:|---:|---:|---:|---:|
| ws3-metaworld-seedexp-latency_aware-method | latency_aware | 300 | 30 | 10.00 | 0.000 | 1.000 | 300.0 |
| ws3-metaworld-seedexp-adaptmanip-method | adaptmanip | 300 | 30 | 10.00 | 0.000 | 1.000 | 300.0 |

Per matched (task, seed) pair, compute delta := success_final(reference)-success_final(comparator). Estimate one-way seed-cluster ICC and design effect; report n_eff := n / design_effect as a conservative dependence diagnostic for Theorem-1 interpretation.
