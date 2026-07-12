# Recent Baseline Official Parity Audit

- Generated (UTC): `2026-03-02T08:20:23Z`
- Variant: `latency_aware`
- Overall status: `no_public_repo_subset_verified`

## Official Source Check

- arXiv id: `2602.14255v1`
- official repo url: `None`
- availability status: `not_found_public_release`
- note: No official repository URL was found in the curated metadata/source snapshot at this checkpoint; rerun this audit each cycle and update when a public release appears.

## Code Link Discovery

- metadata links detected: `0`
- paper-html links detected: `1`
- paper-html links: https://github.com/ValveSoftware/openvr

## 3-Task Shifted Subset Parity

- subset: scenario=`shifted`, tasks=`button-press-v3, push-v3, reach-v3`
- mean: method=0.9333, latency_aware=1.0000, delta=-0.0667 (CI95 halfwidth 0.1307)
- worst-seed: method=0.6667, latency_aware=1.0000, delta=-0.3333
- CVaR40-seed: method=0.8333, latency_aware=1.0000, delta=-0.1667

## Assessment

- reason: No public official repository is currently tracked for latency_aware; software-feasible subset parity check is provided as the reproducible fallback.
- residual risks:
  - Official-code parity cannot be fully closed until an upstream public repository/checkpoint is available.
  - Subset floor deltas are not uniformly positive; monitor next-cycle reruns.
