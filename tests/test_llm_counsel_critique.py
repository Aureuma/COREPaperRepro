from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts/review_readiness/run_llm_counsel_critique.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("run_llm_counsel_critique", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to load run_llm_counsel_critique module spec")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LlmCounselCritiqueTests(unittest.TestCase):
    def test_rounds_are_hard_capped_at_five(self) -> None:
        module = _load_module()
        self.assertEqual(module._resolve_rounds(1), 1)
        self.assertEqual(module._resolve_rounds(5), 5)
        self.assertEqual(module._resolve_rounds(8), 5)
        with self.assertRaises(ValueError):
            module._resolve_rounds(0)

    def test_consensus_reached_on_close_risk_and_overlap(self) -> None:
        module = _load_module()
        gemini = {
            "overall_verdict": "Strong Accept",
            "acceptance_risk_score_0_to_10": 2.0,
            "critical_findings": [
                {
                    "id": "G1",
                    "severity": "high",
                    "issue": "Near parity mean can be misread as weak novelty.",
                    "fix": "Lead with reliability-floor deltas and keep mean secondary.",
                }
            ],
        }
        claude = {
            "overall_verdict": "Strong Accept",
            "acceptance_risk_score_0_to_10": 2.8,
            "critical_findings": [
                {
                    "id": "C1",
                    "severity": "high",
                    "issue": "Reviewers may misread parity means and question novelty.",
                    "fix": "Prioritize reliability floor interpretation over mean-only framing.",
                }
            ],
        }
        metrics = module.evaluate_consensus(
            gemini,
            claude,
            max_risk_delta=1.5,
            min_topic_overlap=0.10,
        )
        self.assertTrue(metrics["consensus_reached"])
        self.assertLessEqual(metrics["risk_delta"], 1.5)
        self.assertGreaterEqual(metrics["topic_overlap"], 0.10)

    def test_consensus_not_reached_on_risk_gap_and_topic_divergence(self) -> None:
        module = _load_module()
        gemini = {
            "overall_verdict": "Strong Accept",
            "acceptance_risk_score_0_to_10": 1.0,
            "critical_findings": [
                {
                    "id": "G1",
                    "severity": "low",
                    "issue": "Minor notation cleanup only.",
                    "fix": "Standardize one symbol in theory section.",
                }
            ],
        }
        claude = {
            "overall_verdict": "Reject",
            "acceptance_risk_score_0_to_10": 7.0,
            "critical_findings": [
                {
                    "id": "C1",
                    "severity": "critical",
                    "issue": "Method lacks external validity due to no transfer tests.",
                    "fix": "Run additional transfer suites and revise claims accordingly.",
                }
            ],
        }
        metrics = module.evaluate_consensus(
            gemini,
            claude,
            max_risk_delta=1.5,
            min_topic_overlap=0.25,
        )
        self.assertFalse(metrics["consensus_reached"])
        self.assertGreater(metrics["risk_delta"], 1.5)
        self.assertLess(metrics["topic_overlap"], 0.25)

    def test_merge_findings_deduplicates(self) -> None:
        module = _load_module()
        gemini = {
            "critical_findings": [
                {
                    "id": "G1",
                    "severity": "high",
                    "issue": "Clarify simulation scope boundaries.",
                    "fix": "State benchmark-only scope in abstract and conclusion.",
                }
            ],
        }
        claude = {
            "top_findings": [
                {
                    "id": "C1",
                    "severity": "high",
                    "issue": "Clarify simulation scope boundaries.",
                    "fix": "State benchmark-only scope in abstract and conclusion.",
                },
                {
                    "id": "C2",
                    "severity": "medium",
                    "issue": "Simplify dense results table.",
                    "fix": "Replace one table with compact inline paragraph summary.",
                },
            ]
        }
        merged = module._merge_consensus_findings(gemini, claude)
        self.assertEqual(len(merged), 2)
        self.assertEqual(merged[0]["source"], "gemini")
        self.assertEqual(merged[1]["source"], "claude")

    def test_council_consensus_with_local_member_tracks_max_pairwise_risk(self) -> None:
        module = _load_module()
        metrics = module.evaluate_council_consensus(
            {
                "gemini": {
                    "overall_verdict": "Strong Accept",
                    "acceptance_risk_score_0_to_10": 2.0,
                    "critical_findings": [
                        {"id": "G1", "severity": "high", "issue": "improve floor framing", "fix": "lead with cvar"}
                    ],
                },
                "claude": {
                    "overall_verdict": "Strong Accept",
                    "acceptance_risk_score_0_to_10": 2.6,
                    "critical_findings": [
                        {"id": "C1", "severity": "high", "issue": "improve floor framing", "fix": "lead with cvar"}
                    ],
                },
                "codex": {
                    "overall_verdict": "Near-ready",
                    "acceptance_risk_score_0_to_10": 5.2,
                    "critical_findings": [
                        {
                            "id": "X1",
                            "severity": "high",
                            "issue": "text claims outpace effect-size evidence",
                            "fix": "tighten claim language in abstract and conclusion",
                        }
                    ],
                },
            },
            max_risk_delta=1.5,
            min_topic_overlap=0.1,
        )
        self.assertIn("codex", metrics["seat_names"])
        self.assertFalse(metrics["consensus_reached"])
        self.assertGreater(metrics["risk_delta"], 1.5)
        self.assertIn("claude|codex", metrics["pairwise_risk_deltas"])

    def test_stale_fallback_uses_latest_provider_artifacts(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            gemini_path = out / "corepaper_gemini_critique_2026-02-22.json"
            claude_path = out / "corepaper_bedrock_claude_critique_2026-02-22.json"
            gemini_path.write_text(
                json.dumps(
                    {
                        "overall_verdict": "Strong Accept",
                        "acceptance_risk_score_0_to_10": 2,
                        "critical_findings": [
                            {"id": "G1", "severity": "high", "issue": "issue one", "fix": "fix one"}
                        ],
                        "next_actions": ["do one"],
                        "residual_risks": ["risk one"],
                    }
                ),
                encoding="utf-8",
            )
            claude_path.write_text(
                json.dumps(
                    {
                        "overall_verdict": "Near-ready",
                        "acceptance_risk_score_0_to_10": 4,
                        "top_findings": [
                            {"id": "C1", "severity": "medium", "issue": "issue two", "fix": "fix two"}
                        ],
                        "next_actions": ["do two"],
                        "residual_risks": ["risk two"],
                    }
                ),
                encoding="utf-8",
            )

            built = module._build_stale_fallback_consensus(
                output_dir=out,
                run_tag="test-run",
                reason="provider failed",
                criteria={"max_risk_delta": 1.5, "min_topic_overlap": 0.2, "max_rounds": 3},
            )
            self.assertIsNotNone(built)
            payload, parsed_path, summary_path = built
            self.assertEqual(payload["mode"], "llm_counsel_stale_fallback")
            self.assertIn("fallback_source_artifacts", payload)
            self.assertTrue(str(parsed_path).endswith("_fallback.json"))
            self.assertTrue(str(summary_path).endswith("_fallback.md"))

    def test_stale_fallback_includes_local_member_when_provided(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / "corepaper_gemini_critique_2026-02-22.json").write_text(
                json.dumps(
                    {
                        "overall_verdict": "Strong Accept",
                        "acceptance_risk_score_0_to_10": 2,
                        "critical_findings": [{"id": "G1", "severity": "high", "issue": "issue one", "fix": "fix one"}],
                        "next_actions": ["do one"],
                        "residual_risks": ["risk one"],
                    }
                ),
                encoding="utf-8",
            )
            (out / "corepaper_bedrock_claude_critique_2026-02-22.json").write_text(
                json.dumps(
                    {
                        "overall_verdict": "Near-ready",
                        "acceptance_risk_score_0_to_10": 4,
                        "top_findings": [{"id": "C1", "severity": "medium", "issue": "issue two", "fix": "fix two"}],
                        "next_actions": ["do two"],
                        "residual_risks": ["risk two"],
                    }
                ),
                encoding="utf-8",
            )
            local_path = out / "codex_local.json"
            local_payload = {
                "overall_verdict": "Near-ready",
                "acceptance_risk_score_0_to_10": 3.5,
                "critical_findings": [{"id": "X1", "severity": "high", "issue": "issue three", "fix": "fix three"}],
                "next_actions": ["do three"],
                "residual_risks": ["risk three"],
            }
            local_path.write_text(json.dumps(local_payload), encoding="utf-8")

            built = module._build_stale_fallback_consensus(
                output_dir=out,
                run_tag="test-run",
                reason="provider failed",
                criteria={"max_risk_delta": 1.5, "min_topic_overlap": 0.2, "max_rounds": 3},
                local_member_label="codex",
                local_member_payload=local_payload,
                local_member_source_path=local_path,
            )
            self.assertIsNotNone(built)
            payload, _, _ = built
            self.assertEqual(payload["local_member"]["label"], "codex")
            self.assertIn("codex", payload["council_seats"])
            self.assertIn("local_member_source", payload["fallback_source_artifacts"])

    def test_gemini_batch_manifest_includes_improvement_directive(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            output_dir = tmp_dir / "out"
            output_dir.mkdir(parents=True, exist_ok=True)

            with mock.patch.object(module, "_run_cmd", return_value=(0, "gemini.log")):
                module._run_gemini_batch(
                    paper_pdf=tmp_dir / "paper.pdf",
                    paper_tex=tmp_dir / "paper.tex",
                    plan_md=tmp_dir / "plan.md",
                    output_dir=output_dir,
                    model="gemini-3.1-pro-preview",
                    schema_mode="compact",
                    max_output_tokens=1024,
                    improvement_directive="improve rigor and visuals",
                    tag="unit-g",
                    peer_context_json=None,
                )

            manifest = json.loads((output_dir / "corepaper_counsel_gemini_manifest_unit-g.json").read_text())
            self.assertEqual(manifest["jobs"][0]["improvement_directive"], "improve rigor and visuals")

    def test_claude_batch_manifest_includes_improvement_directive(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            output_dir = tmp_dir / "out"
            output_dir.mkdir(parents=True, exist_ok=True)

            with mock.patch.object(module, "_run_cmd", return_value=(0, "claude.log")):
                module._run_claude_batch(
                    paper_pdf=tmp_dir / "paper.pdf",
                    paper_tex=tmp_dir / "paper.tex",
                    plan_md=tmp_dir / "plan.md",
                    output_dir=output_dir,
                    model="us.anthropic.claude-opus-4-6-v1",
                    region="us-east-1",
                    backend="boto3",
                    schema_mode="compact",
                    max_output_tokens=1024,
                    improvement_directive="improve theory and evidence",
                    tag="unit-c",
                    peer_context_json=None,
                )

            manifest = json.loads((output_dir / "corepaper_counsel_claude_manifest_unit-c.json").read_text())
            self.assertEqual(manifest["jobs"][0]["improvement_directive"], "improve theory and evidence")


if __name__ == "__main__":
    unittest.main()
