# CORE: Uncertainty-Gated Policy Optimization for Robust Contact-Rich Manipulation

## Abstract
We present CORE, an uncertainty-gated policy optimization method for contact-rich manipulation under distribution shift.
In the current multiseed benchmark slice, our method reaches 0.7494 success versus baseline 0.7119 (+0.0375).
Results are currently benchmark-scoped and include explicit failure and limitation tracking.

## 1. Introduction
Robust contact-rich manipulation under distribution shift remains difficult to evaluate and iterate safely.

## 2. Related Work
Recent robust planning/manipulation work is tracked in weekly literature briefs and mapped to novelty comparisons.

## 3. Method
CORE combines uncertainty-penalized trust-region updates with an online promote/rollback gate to reject unstable policy steps.

## 4. Experimental Setup
We use fixed-seed suites and consistent run budgets across baseline and method variants.

## 5. Results
Main benchmark: baseline=0.7119, method=0.7494, delta=+0.0375.
Ablation and robustness results are reported in WS5 artifacts.

## 6. Discussion and Limitations
Current evidence is strong for the benchmark stack with software-transfer stress validation, while exact upstream baseline parity remains future work.

## 7. Conclusion
Uncertainty-gated updates improve robustness in benchmark-scoped software validation and support conservative, evidence-backed claims.

