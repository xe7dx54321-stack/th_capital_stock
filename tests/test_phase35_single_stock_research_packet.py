import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase35_single_stock_research_packet import build_payload, render_markdown
from phase34_helpers import make_phase34_conn


class Phase35SingleStockResearchPacketTests(unittest.TestCase):
    def test_packet_has_complete_sections_and_promotion_boundary(self):
        payload = build_payload(make_phase34_conn(), ticker="300394.SZ")
        packet = payload["single_stock_research_packet"]
        for key in (
            "research_thesis",
            "evidence_chain",
            "variable_matrix",
            "expectation_gap",
            "valuation_support",
            "bear_case",
            "research_quality",
            "research_scenarios",
            "why_not_pending",
            "next_evidence_plan",
        ):
            self.assertIn(key, packet)
        self.assertFalse(packet["promotion_boundary"]["promotion_allowed"])
        self.assertFalse(packet["promotion_boundary"]["new_pending_created"])
        text = json.dumps(payload, ensure_ascii=False).lower() + render_markdown(payload).lower()
        self.assertNotIn("buy recommendation", text)
        self.assertNotIn("sell recommendation", text)


if __name__ == "__main__":
    unittest.main()
