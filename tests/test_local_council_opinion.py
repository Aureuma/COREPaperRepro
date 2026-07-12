from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts/review_readiness/generate_local_council_opinion.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("generate_local_council_opinion", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to load generate_local_council_opinion module spec")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LocalCouncilOpinionTests(unittest.TestCase):
    def test_build_findings_flags_subsection_usage(self) -> None:
        module = _load_module()
        findings, risk = module._build_findings(
            paper_text="\\section{A}\\subsection{B}\\begin{theorem}x\\end{theorem} Proof.",
            plan_text="| ID | Status |",
            parity_report=Path("/tmp/does-not-exist.json"),
        )
        ids = {row["id"] for row in findings}
        self.assertIn("CDX-01", ids)
        self.assertGreaterEqual(risk, 5.0)

    def test_main_writes_expected_schema(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            paper_tex = tmp_dir / "paper.tex"
            plan_md = tmp_dir / "plan.md"
            out_json = tmp_dir / "local.json"
            paper_tex.write_text(
                "\\section{Theory}\\begin{theorem}x\\end{theorem}\\textit{Proof.} simulation-only floor CVaR worst",
                encoding="utf-8",
            )
            plan_md.write_text("| ID | Status |\n|---|---|\n| A | Not done |\n", encoding="utf-8")

            args = [
                "prog",
                "--paper-tex",
                str(paper_tex),
                "--plan-md",
                str(plan_md),
                "--output-json",
                str(out_json),
            ]
            with mock.patch("sys.argv", args):
                rc = module.main()
            self.assertEqual(rc, 0)
            payload = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertIn("overall_verdict", payload)
            self.assertIn("acceptance_risk_score_0_to_10", payload)
            self.assertIn("top_findings", payload)
            self.assertIn("next_actions", payload)


if __name__ == "__main__":
    unittest.main()
