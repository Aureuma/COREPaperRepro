# Proposition-2 Ordering Proxy (Auto-generated)

- Source logs: `output/corepaper_logs/experiments/recent_baselines_latest`
- Reference variant (candidate proxy): `method`
- Total paired rows: 168
- Overall hold rate: 0.250
- Overall violation rate: 0.750

| Comparator (incumbent proxy) | Paired rows | Hold rate | Violation rate | Mean(U_inc-U_cand) | Max|U_inc-U_cand| |
|---|---:|---:|---:|---:|---:|
| adaptmanip | 84 | 0.167 | 0.833 | +0.0040 | 0.0069 |
| latency_aware | 84 | 0.333 | 0.667 | +0.0022 | 0.0098 |

Note: this is an observability proxy on matched benchmark rows, not a direct per-iteration training-log replay.
