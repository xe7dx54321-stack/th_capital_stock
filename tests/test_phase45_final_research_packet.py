import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from phase45_helpers import make_phase45_conn
from build_phase45_final_research_packet import build_payload, render_markdown


class Phase45FinalResearchPacketTests(unittest.TestCase):
    def test_final_packet_is_complete_without_paper_order(self):
        payload = build_payload(make_phase45_conn(), "300308.SZ")
        packet = payload["final_research_packet"]
        for key in (
            "asset_summary",
            "thesis_review",
            "evidence_sufficiency",
            "variable_coverage",
            "expectation_gap_valuation_boundary",
            "bear_case_review",
            "final_research_conclusion",
            "paper_watchlist_readiness",
            "why_not_pending",
            "next_tracking_plan",
        ):
            self.assertIn(key, packet)
        self.assertEqual(packet["promotion_boundary"]["paper_order_created"], 0)
        self.assertEqual(packet["promotion_boundary"]["pending_created"], 0)
        self.assertIn("Why Not Pending", render_markdown(payload))


if __name__ == "__main__":
    unittest.main()
