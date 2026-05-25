import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERIFICATION_DIR = ROOT / "08_scripts" / "verification"
if str(VERIFICATION_DIR) not in sys.path:
    sys.path.insert(0, str(VERIFICATION_DIR))

from validate_phase14_thesis_aware_multi_ticker_live import summarize_results


class Phase14MultiTickerThesisAwareTests(unittest.TestCase):
    def test_summary_counts_thesis_and_reduced_size_pending(self):
        summary = summarize_results(
            "ai_core",
            [
                {
                    "ticker": "09988.HK",
                    "primary_thesis_type": "valuation_rerating",
                    "after_status": "pending_human_review",
                    "promotion_mode": "reduced_size_pending",
                    "core_blockers": [],
                    "optional_warnings": ["capex", "free_cash_flow"],
                },
                {
                    "ticker": "300308.SZ",
                    "primary_thesis_type": "unknown",
                    "after_status": "candidate_shadow",
                    "core_blockers": [],
                    "optional_warnings": [],
                },
                {
                    "ticker": "TEST",
                    "primary_thesis_type": "cash_flow_improvement",
                    "after_status": "candidate_shadow",
                    "core_blockers": ["capex"],
                    "optional_warnings": [],
                },
            ],
        )

        self.assertEqual(summary["pending_human_review"], 1)
        self.assertEqual(summary["reduced_size_pending"], 1)
        self.assertEqual(summary["unknown_thesis_count"], 1)
        self.assertEqual(summary["core_blocker_count"], 1)
        self.assertEqual(summary["non_core_warning_count"], 2)


if __name__ == "__main__":
    unittest.main()
