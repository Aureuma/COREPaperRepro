# Ceiling-Regime Diagnostics (Auto-generated)

## Thresholds

- mean gap threshold: 0.0600
- floor gap threshold: 0.0300
- ceiling mean threshold: 0.6200

## MetaWorld N=30 (method vs latency_aware)

| Metric | Value |
|---|---:|
| Mean gap | +0.0533 |
| Min floor gap (worst/CVaR) | +0.0000 |
| Reference mean | 0.7133 |
| p-value | 0.1875 |
| Mean near-parity | YES |
| Floor separation positive | NO |
| Ceiling level high | YES |
| Expected ceiling regime | NO |

## Stress Aggregate Cross-check

| Top variant | Runner-up | Mean gap | Min floor gap |
|---|---|---:|---:|
| method | adaptmanip | +0.0071 | +0.0079 |

- Interpretation: Ceiling-regime criteria are not fully satisfied under configured thresholds.
- Recommendation: Prioritize worst-seed/CVaR and tail-risk metrics over mean-only interpretation.
