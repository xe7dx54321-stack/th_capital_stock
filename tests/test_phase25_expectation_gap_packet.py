import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
REPORTING_DIR = ROOT / "08_scripts" / "reporting"
TEST_DIR = ROOT / "tests"
for path in (LIB_DIR, REPORTING_DIR, TEST_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase25_supply_chain_expectation_gap_packet import build_packet, render_markdown
from test_phase25_end_demand_proxy import make_evidence_conn


class Phase25ExpectationGapPacketTests(unittest.TestCase):
    def test_packet_exposes_assumptions_and_blocks_promotion(self):
        packet = build_packet(make_evidence_conn(), "300394.SZ")
        self.assertEqual(packet["ticker"], "300394.SZ")
        self.assertIn("official consensus", packet["sections"]["missing_variables"])
        self.assertFalse(packet["promotion_allowed"])
        self.assertTrue(packet["safety"]["assumptions_transparent"])
        self.assertIn("# Supply Chain Expectation Gap Packet", render_markdown(packet))


if __name__ == "__main__":
    unittest.main()
