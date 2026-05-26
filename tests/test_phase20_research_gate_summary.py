import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTING_DIR = ROOT / "08_scripts" / "reporting"
if str(REPORTING_DIR) not in sys.path:
    sys.path.insert(0, str(REPORTING_DIR))

from build_phase20_research_gate_summary import compact_payload, render_markdown


class Phase20ResearchGateSummaryTests(unittest.TestCase):
    def test_research_gate_summary_outputs_gate_improvements(self):
        payload = compact_payload(
            {
                "generated_at": "2026-05-26 00:00:00",
                "summary": {
                    "bear_case_gate_improved": 1,
                    "valuation_gate_improved": 1,
                    "proxy_gate_improved": 0,
                    "thesis_evidence_improved": 1,
                },
                "ticker_results": [
                    {
                        "ticker": "300308.SZ",
                        "after_status": "candidate_shadow",
                        "primary_gate_before": "BEAR_CASE_GATE",
                        "bear_case_status_after": "requires_more_evidence",
                        "valuation_status_after": "blocked",
                        "proxy_status_after": "medium",
                        "thesis_status_after": "ai_infrastructure_demand",
                        "why_no_pending": ["bear case remains blocking"],
                    }
                ],
            },
            "ai_core",
        )
        markdown = render_markdown(payload)

        self.assertEqual(payload["summary"]["gate_improvements"]["bear_case"], 1)
        self.assertEqual(payload["summary"]["primary_blocking_gates"]["BEAR_CASE_GATE"], 1)
        self.assertIn("Phase 20 Research Gate Summary", markdown)
        self.assertIn("300308.SZ", markdown)


if __name__ == "__main__":
    unittest.main()
