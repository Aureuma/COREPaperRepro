# CORE Paper Notation Guide

This is the notation reference for the consolidated manuscript at `paper/manuscript.tex`.

## Usage Rules

- Reuse symbols exactly as defined here; avoid introducing aliases.
- Keep rollout-level quantities (`\tau`, `R`) separate from update-level quantities (`k`, `\Delta_k`, `U_k`).
- Use triage thresholds consistently as `\tau_{\text{green}}` and `\tau_{\text{yellow}}` with `\tau_{\text{yellow}} < \tau_{\text{green}}`; avoid alias symbols.
- Report CVaR consistently as `\mathrm{CVaR}_{\alpha}` with `\alpha=0.4` when discussing `\mathrm{CVaR}_{40}` metrics.

## Core Symbols

| Concept | Symbol | LaTeX | Brief definition | Notes / cautions |
|---|---|---|---|---|
| Latent state | \(s_t\) | `s_t` | Environment state at time \(t\) | Not directly observed. |
| Observation | \(o_t\) | `o_t` | Observation at time \(t\) | Use for policy inputs. |
| Action | \(a_t\) | `a_t` | Action at time \(t\) | Keep action domain implicit unless needed. |
| History | \(h_t\) | `h_t` | Policy history \((o_{0:t}, a_{0:t-1})\) | Use for partial observability framing. |
| Shift variable | \(\xi\) | `\\xi` | Distribution-shift condition | Sampled from \(p(\xi)\). |
| Shift distribution | \(p(\xi)\) | `p(\\xi)` | Distribution over shift conditions | Distinct from policy distributions. |
| Policy | \(\pi_\theta\) | `\\pi_\\theta` | Policy parameterized by \(\theta\) | Use \(\theta_k\) for iteration-indexed params. |
| Trajectory | \(\tau\) | `\\tau` | Rollout trajectory | Avoid reusing \(\tau\) for thresholds. |
| Return | \(R(\tau,\xi)\) | `R(\\tau,\\xi)` | Discounted return under shift | Defined as \(\sum_t \gamma^t r_t\). |
| Objective | \(J(\theta)\) | `J(\\theta)` | Risk-aware optimization objective | Keep separate from surrogate \(\hat{J}_k\). |
| Surrogate objective | \(\hat{J}_k(\theta)\) | `\\hat{J}_k(\\theta)` | Iteration-\(k\) local surrogate | Used in update rule and \(\hat{\Delta}_k\). |
| Discount factor | \(\gamma\) | `\\gamma` | Discount on rewards | Standard RL notation. |
| Risk weight | \(\lambda\) | `\\lambda` | Weight on CVaR term | Keep nonnegative. |
| CVaR tail level | \(\alpha\) | `\\alpha` | Tail fraction for CVaR | Paper metrics use \(\alpha=0.4\). |
| Ensemble value head | \(Q_{\phi_k}^{(m)}\) | `Q_{\\phi_k}^{(m)}` | \(m\)-th value head at iter \(k\) | Use \(m=1,\dots,M\). |
| Ensemble size | \(M\) | `M` | Number of bootstrap value heads | Fixed to 5 in experiments. |
| Rollout batch | \(\mathcal{B}_k\) | `\\mathcal{B}_k` | Batch for update iteration \(k\) | Used to compute uncertainty. |
| Uncertainty score | \(U_k(\theta)\) | `U_k(\\theta)` | Ensemble-disagreement uncertainty | Core gating signal. |
| KL radius | \(\varepsilon\) | `\\varepsilon` | Trust-region bound | From constrained update. |
| Uncertainty penalty | \(\beta\) | `\\beta` | Weight on uncertainty in surrogate | Keep interpretation as regularizer. |
| Surrogate gain | \(\hat{\Delta}_k\) | `\\hat{\\Delta}_k` | Surrogate improvement at iteration \(k\) | Before uncertainty correction. |
| Lower-bound proxy | \(\underline{\Delta}_k\) | `\\underline{\\Delta}_k` | Conservative improvement proxy | Drives promote/rollback decision. |
| Floor threshold | \(\tau_{\mathrm{floor},k}\) | `\\tau_{\\mathrm{floor},k}` | Matched-seed per-update floor certificate threshold | Used in the empirical floor theorem. |
| Error envelope constants | \(c_u, c_0\) | `c_u`, `c_0` | Uncertainty-dominance coefficients | Empirical fit values reported in experiments. |
| Green threshold | \(\tau_{\text{green}}\) | `\\tau_{\\text{green}}` | Promote threshold in implementation/theory | Use this symbol everywhere. |
| Yellow threshold | \(\tau_{\text{yellow}}\) | `\\tau_{\\text{yellow}}` | Monitor-zone threshold | Must satisfy \(\tau_{\text{yellow}} < \tau_{\text{green}}\). |

## Gating Semantics

- Green: `\underline{\Delta}_k \ge \tau_{\text{green}}` -> promote candidate update.
- Yellow: `\tau_{\text{yellow}} \le \underline{\Delta}_k < \tau_{\text{green}}` -> hold incumbent policy and run short monitor recheck.
- Red: `\underline{\Delta}_k < \tau_{\text{yellow}}` -> rollback candidate and pivot hyperparameters.
- `\hat{\Delta}_k` and `U_k(\theta_{k+1})` must be estimated from the same matched-seed diagnostic set `\mathcal{S}_k`.

## Writing Consistency Checklist

- If a symbol appears in abstract/introduction, ensure it is defined or referenced in Theory.
- Use “reliability floor” only with explicit metrics (worst-seed, CVaR, tail count).
- Avoid mixing “benchmark performance” and “mechanism diagnostics” language in the same claim sentence.
