from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class MetaworldSliceStatsTests(unittest.TestCase):
    def test_outputs_include_cvar_and_worst_seed_pvalues(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            input_json = tmp / "slice.json"
            output_json = tmp / "stats.json"
            output_md = tmp / "stats.md"

            episodes = []
            for seed, method_vals, ext2_vals in (
                (1, [0.8, 0.7], [0.5, 0.4]),
                (2, [0.9, 0.8], [0.6, 0.5]),
                (3, [0.85, 0.75], [0.55, 0.45]),
            ):
                for val in method_vals:
                    episodes.append(
                        {
                            "task": "reach-v3",
                            "scenario": "shifted",
                            "variant": "method",
                            "seed": seed,
                            "success_final": val,
                            "steps_executed": 80,
                        }
                    )
                for val in ext2_vals:
                    episodes.append(
                        {
                            "task": "reach-v3",
                            "scenario": "shifted",
                            "variant": "ext2",
                            "seed": seed,
                            "success_final": val,
                            "steps_executed": 80,
                        }
                    )

            input_json.write_text(json.dumps({"episodes": episodes}), encoding="utf-8")
            subprocess.run(
                [
                    "python3",
                    "scripts/experiments/analyze_metaworld_slice_stats.py",
                    "--input-json",
                    str(input_json),
                    "--output-json",
                    str(output_json),
                    "--output-md",
                    str(output_md),
                    "--scenario",
                    "shifted",
                    "--reference-group",
                    "method",
                    "--comparators",
                    "ext2",
                    "--max-exact-combinations",
                    "1000000",
                    "--mc-samples",
                    "2000",
                ],
                cwd=REPO_ROOT,
                check=True,
            )

            payload = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertIn("comparisons", payload)
            self.assertEqual(len(payload["comparisons"]), 1)
            row = payload["comparisons"][0]
            for key in ("p_two_sided_mean", "p_two_sided_worst_seed", "p_two_sided_cvar40_seed"):
                self.assertIn(key, row)
                self.assertGreaterEqual(float(row[key]), 0.0)
                self.assertLessEqual(float(row[key]), 1.0)


class BaselineImplementationDetailsTests(unittest.TestCase):
    def test_outputs_include_library_hash_and_hyperparameter_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            output_json = tmp / "details.json"
            output_md = tmp / "details.md"
            subprocess.run(
                [
                    "python3",
                    "scripts/experiments/generate_baseline_implementation_details.py",
                    "--output-json",
                    str(output_json),
                    "--output-md",
                    str(output_md),
                ],
                cwd=REPO_ROOT,
                check=True,
            )
            payload = json.loads(output_json.read_text(encoding="utf-8"))
            self.assertIn("library_lane_hyperparameters", payload)
            self.assertIn("library_config_hashes", payload)
            self.assertGreaterEqual(len(payload["library_config_hashes"]), 3)
            variant_names = {row["variant"] for row in payload["library_lane_hyperparameters"]["profiles"]}
            self.assertIn("sb3_ppo", variant_names)
            self.assertIn("rllib_sac", variant_names)
            self.assertIn("method", variant_names)


if __name__ == "__main__":
    unittest.main()
