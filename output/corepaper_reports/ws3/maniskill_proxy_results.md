# ManiSkill-Proxy Slice Results (Auto-generated)

- Benchmark family: `maniskill-proxy`
- Config: `config/benchmarks/experiments_maniskill_proxy_recent.json`
- JSON report: `output/corepaper_reports/ws3/maniskill_proxy_results.json`
- Tasks: `pick_cube, stack_cube, peg_insert, drawer_open, button_press, door_unlock, cable_route, bimanual_handover`

## Scenario-Level Summary

| Scenario | Variant | N | Mean Success | Worst-Seed | CVaR40 | Mean Steps | Success / 1k Steps |
|---|---|---:|---:|---:|---:|---:|---:|
| nominal | baseline | 64 | 0.5387 | 0.4730 | 0.5117 | 77.56 | 6.946 |
| nominal | ext1 | 64 | 0.5669 | 0.5222 | 0.5418 | 77.20 | 7.343 |
| nominal | ext2 | 64 | 0.5840 | 0.5300 | 0.5568 | 76.95 | 7.588 |
| nominal | latency_aware | 64 | 0.5884 | 0.5444 | 0.5632 | 77.39 | 7.602 |
| nominal | adaptmanip | 64 | 0.5924 | 0.5465 | 0.5646 | 77.20 | 7.674 |
| nominal | robust_cp | 64 | 0.5825 | 0.5288 | 0.5571 | 77.12 | 7.553 |
| nominal | method | 64 | 0.6002 | 0.5570 | 0.5744 | 76.80 | 7.816 |
| shifted | baseline | 64 | 0.3226 | 0.2762 | 0.2975 | 86.77 | 3.718 |
| shifted | ext1 | 64 | 0.3639 | 0.3191 | 0.3374 | 87.00 | 4.183 |
| shifted | ext2 | 64 | 0.3946 | 0.3489 | 0.3678 | 87.27 | 4.522 |
| shifted | latency_aware | 64 | 0.4002 | 0.3489 | 0.3732 | 86.83 | 4.609 |
| shifted | adaptmanip | 64 | 0.4026 | 0.3531 | 0.3741 | 86.70 | 4.644 |
| shifted | robust_cp | 64 | 0.4025 | 0.3574 | 0.3765 | 87.39 | 4.606 |
| shifted | method | 64 | 0.4277 | 0.3793 | 0.4009 | 86.66 | 4.935 |
