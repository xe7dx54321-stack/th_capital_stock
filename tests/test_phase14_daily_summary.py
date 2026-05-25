import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTING_DIR = ROOT / "08_scripts" / "reporting"
if str(REPORTING_DIR) not in sys.path:
    sys.path.insert(0, str(REPORTING_DIR))

from build_phase14_thesis_aware_daily_summary import build_summary_payload, render_markdown


class Phase14DailySummaryTests(unittest.TestCase):
    def test_daily_summary_separates_core_non_core_and_unknown(self):
        payload = build_summary_payload(
            {
                "watchlist_id": "ai_core",
                "tickers": [
                    {
                        "ticker": "09988.HK",
                        "primary_thesis_type": "valuation_rerating",
                        "after_status": "pending_human_review",
                        "promotion_mode": "reduced_size_pending",
                        "action": "small_candidate",
                        "suggested_position_pct": 0.75,
                        "core_blockers": [],
                        "optional_warnings": ["capex"],
                        "bear_case_gate": {"overall_status": "partially_mitigated"},
                    },
                    {
                        "ticker": "TEST",
                        "primary_thesis_type": "cash_flow_improvement",
                        "after_status": "candidate_shadow",
                        "core_blockers": ["free_cash_flow"],
                    },
                    {
                        "ticker": "UNKNOWN",
                        "primary_thesis_type": "unknown",
                        "after_status": "candidate_shadow",
                    },
                ],
                "summary": {"overall_result": "partial_pass"},
            },
            "ai_core",
        )
        markdown = render_markdown(payload)

        self.assertEqual(payload["summary"]["reduced_size_pending"], 1)
        self.assertEqual(payload["summary"]["unknown_thesis"], 1)
        self.assertEqual(payload["summary"]["core_blocker_tickers"], ["TEST"])
        self.assertEqual(payload["summary"]["non_core_warning_tickers"], ["09988.HK"])
        self.assertIn("Phase 14 Thesis-aware Daily Summary", markdown)
        self.assertIn("09988.HK", markdown)


if __name__ == "__main__":
    unittest.main()
