import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTING_DIR = ROOT / "08_scripts" / "reporting"
if str(REPORTING_DIR) not in sys.path:
    sys.path.insert(0, str(REPORTING_DIR))

from build_phase22_valuation_demand_gate_summary import compact_payload, render_markdown


class Phase22ValuationDemandSummaryTests(unittest.TestCase):
    def test_summary_outputs_json_and_markdown(self):
        payload = compact_payload(
            {
                "generated_at": "2026-05-26 10:00:00",
                "summary": {
                    "valuation_gate_improved": 1,
                    "proxy_strengthened": 1,
                    "new_reduced_size_pending": 0,
                },
                "ticker_results": [
                    {
                        "ticker": "688041.SH",
                        "valuation_after": "reduced_size_supporting",
                        "demand_valuation_linkage": "medium_support",
                        "confirmed_order_count": 0,
                        "proxy_after": "medium",
                        "after_status": "candidate_shadow",
                        "primary_gate_before": "VALUATION_GATE",
                        "why_no_pending": ["find confirmed order/tender evidence"],
                        "remaining_warnings": ["FORWARD_EPS_PROXY_ONLY"],
                    }
                ],
                "safety": {"promotion_rules_relaxed": False},
            },
            "ai_core",
        )
        markdown = render_markdown(payload)

        self.assertEqual(payload["summary"]["valuation_gate_improved"], 1)
        self.assertEqual(payload["rows"][0]["demand_evidence"], "medium_support")
        self.assertIn("Phase 22 Valuation / Demand Gate Summary", markdown)
        self.assertIn("688041.SH", markdown)


if __name__ == "__main__":
    unittest.main()
