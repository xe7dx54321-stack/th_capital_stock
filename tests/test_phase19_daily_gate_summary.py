import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTING_DIR = ROOT / "08_scripts" / "reporting"
if str(REPORTING_DIR) not in sys.path:
    sys.path.insert(0, str(REPORTING_DIR))

from build_phase19_daily_gate_summary import compact_payload, render_markdown


class Phase19DailyGateSummaryTests(unittest.TestCase):
    def test_daily_gate_summary_outputs_distribution(self):
        payload = compact_payload(
            {
                "generated_at": "2026-05-26T00:00:00",
                "summary": {"pending_human_review": 0, "candidate_shadow": 2, "observation_only": 0, "core_blocker_count": 0},
                "ticker_results": [
                    {
                        "ticker": "00700.HK",
                        "status": "candidate_shadow",
                        "primary_thesis_type": "valuation_rerating",
                        "primary_blocking_gate": "BEAR_CASE_GATE",
                        "core_blockers": [],
                        "recovered_fields": ["shareholders_equity"],
                        "next_fix": ["strengthen bear case response"],
                    },
                    {
                        "ticker": "002230.SZ",
                        "status": "candidate_shadow",
                        "primary_thesis_type": "unknown",
                        "primary_blocking_gate": "THESIS_CONFIDENCE_GATE",
                        "core_blockers": [],
                        "recovered_fields": [],
                        "next_fix": ["build thesis evidence gate"],
                    },
                ],
            },
            "ai_core",
        )
        markdown = render_markdown(payload)

        self.assertEqual(payload["summary"]["primary_blocking_gates"]["BEAR_CASE_GATE"], 1)
        self.assertEqual(payload["summary"]["primary_blocking_gates"]["THESIS_CONFIDENCE_GATE"], 1)
        self.assertIn("Phase 19 Daily Gate Summary", markdown)
        self.assertIn("00700.HK", markdown)


if __name__ == "__main__":
    unittest.main()
