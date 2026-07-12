from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts/experiments/audit_recent_baseline_official_parity.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("audit_recent_baseline_official_parity", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to load audit_recent_baseline_official_parity module spec")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RecentBaselineOfficialParityTests(unittest.TestCase):
    def test_extract_urls_filters_non_code_hosts(self) -> None:
        module = _load_module()
        text = (
            "See https://example.com/docs and https://github.com/org/repo plus "
            "https://gitlab.com/group/proj and https://huggingface.co/spaces/demo"
        )
        urls = module._extract_urls(text)
        self.assertIn("https://github.com/org/repo", urls)
        self.assertIn("https://gitlab.com/group/proj", urls)
        self.assertIn("https://huggingface.co/spaces/demo", urls)
        self.assertNotIn("https://example.com/docs", urls)

    def test_subset_metrics_computes_floor_deltas(self) -> None:
        module = _load_module()
        rows = [
            {"task": "reach-v3", "scenario": "shifted", "variant": "method", "seed": 1, "success_final": 0.80},
            {"task": "reach-v3", "scenario": "shifted", "variant": "latency_aware", "seed": 1, "success_final": 0.74},
            {"task": "push-v3", "scenario": "shifted", "variant": "method", "seed": 2, "success_final": 0.78},
            {"task": "push-v3", "scenario": "shifted", "variant": "latency_aware", "seed": 2, "success_final": 0.75},
            {
                "task": "button-press-v3",
                "scenario": "shifted",
                "variant": "method",
                "seed": 3,
                "success_final": 0.79,
            },
            {
                "task": "button-press-v3",
                "scenario": "shifted",
                "variant": "latency_aware",
                "seed": 3,
                "success_final": 0.73,
            },
        ]
        metrics = module._build_subset_metrics(
            rows=rows,
            tasks=("reach-v3", "push-v3", "button-press-v3"),
            scenario="shifted",
            reference_variant="method",
            comparator_variant="latency_aware",
        )
        self.assertEqual(metrics["task_count"], 3)
        self.assertGreater(metrics["delta_mean"], 0.0)
        self.assertGreater(metrics["delta_worst_seed_mean"], 0.0)
        self.assertGreater(metrics["delta_cvar40_seed"], 0.0)


if __name__ == "__main__":
    unittest.main()
