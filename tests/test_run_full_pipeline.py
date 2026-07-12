from __future__ import annotations

import argparse
import importlib.util
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts/paper/run_full_pipeline.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("run_full_pipeline", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to load run_full_pipeline module spec")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RunFullPipelineTests(unittest.TestCase):
    def test_default_flow_runs_counsel_critique(self) -> None:
        module = _load_module()
        args = argparse.Namespace(
            no_auto_bump=True,
            bump_part="patch",
            with_critiques=True,
            strict_critiques=False,
            skip_lock_refresh=False,
        )

        step_names: list[str] = []
        artifact_checks: list[str] = []

        with (
            mock.patch.object(module, "parse_args", return_value=args),
            mock.patch.object(module, "run_step", side_effect=lambda name, cmd: step_names.append(name)),
            mock.patch.object(module, "require_artifacts", side_effect=lambda name, artifacts: artifact_checks.append(name)),
            mock.patch.object(module, "maybe_run_critique_step", return_value=True) as critique_mock,
        ):
            rc = module.main()

        self.assertEqual(rc, 0)
        self.assertEqual(
            step_names,
            [
                "version-sync-preflight",
                "experiments-cycle",
                "figures",
                "build-pdf",
                "validate",
                "sanity-checks-pre-bump",
                "local-council-opinion",
            ],
        )
        self.assertEqual(
            artifact_checks,
            ["experiments-cycle", "figures", "build-pdf", "validate", "local-council-opinion"],
        )
        self.assertEqual(critique_mock.call_count, 1)
        self.assertEqual(critique_mock.call_args_list[0].args[0], "llm-counsel-critique")
        counsel_cmd = critique_mock.call_args_list[0].args[1]
        self.assertIn("scripts/review_readiness/run_llm_counsel_critique.py", counsel_cmd)
        self.assertIn("--gemini-model", counsel_cmd)
        self.assertIn("gemini-3.1-pro-preview", counsel_cmd)
        self.assertIn("--claude-model", counsel_cmd)
        self.assertIn("us.anthropic.claude-opus-4-6-v1", counsel_cmd)
        self.assertIn("--claude-backend", counsel_cmd)
        self.assertIn("boto3", counsel_cmd)
        self.assertIn("--rounds", counsel_cmd)
        self.assertIn("5", counsel_cmd)
        self.assertIn("--council-local-opinion-json", counsel_cmd)
        self.assertIn("output/corepaper_reports/review_readiness/corepaper_local_council_opinion_latest.json", counsel_cmd)
        self.assertIn("--council-local-opinion-label", counsel_cmd)
        self.assertIn("codex", counsel_cmd)
        self.assertIn("--allow-stale-fallback", counsel_cmd)

    def test_no_critiques_and_bump_runs_when_enabled(self) -> None:
        module = _load_module()
        args = argparse.Namespace(
            no_auto_bump=False,
            bump_part="minor",
            with_critiques=False,
            strict_critiques=False,
            skip_lock_refresh=True,
        )

        step_names: list[str] = []

        with (
            mock.patch.object(module, "parse_args", return_value=args),
            mock.patch.object(module, "run_step", side_effect=lambda name, cmd: step_names.append(name)),
            mock.patch.object(module, "require_artifacts", return_value=None),
            mock.patch.object(module, "read_version", side_effect=["1.2.3", "1.3.0"]),
            mock.patch.object(module, "maybe_run_critique_step", return_value=True) as critique_mock,
        ):
            rc = module.main()

        self.assertEqual(rc, 0)
        self.assertNotIn("uv-lock-refresh", step_names)
        self.assertIn("version-bump-minor", step_names)
        self.assertIn("regenerate-macros", step_names)
        self.assertIn("sanity-checks-post-bump", step_names)
        critique_mock.assert_not_called()

    def test_bump_must_change_version(self) -> None:
        module = _load_module()
        args = argparse.Namespace(
            no_auto_bump=False,
            bump_part="patch",
            with_critiques=False,
            strict_critiques=False,
            skip_lock_refresh=True,
        )

        with (
            mock.patch.object(module, "parse_args", return_value=args),
            mock.patch.object(module, "run_step", return_value=None),
            mock.patch.object(module, "require_artifacts", return_value=None),
            mock.patch.object(module, "read_version", side_effect=["2.0.0", "2.0.0"]),
            mock.patch.object(module, "maybe_run_critique_step", return_value=True),
        ):
            with self.assertRaises(RuntimeError):
                module.main()


if __name__ == "__main__":
    unittest.main()
