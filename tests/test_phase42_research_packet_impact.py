import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "verification", ROOT / "08_scripts" / "reporting", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from validate_phase42_research_packet_impact import build_payload
from phase42_helpers import make_phase42_conn


class Phase42ResearchPacketImpactTests(unittest.TestCase):
    def test_research_packet_impact_does_not_strong_upgrade(self):
        payload = build_payload(make_phase42_conn(), "300308.SZ")
        impact = payload["research_packet_impact"]
        self.assertEqual(payload["overall_status"], "pass")
        self.assertFalse(impact["official_consensus_added"])
        self.assertFalse(impact["supplier_share_confirmed"])
        self.assertFalse(impact["customer_allocation_confirmed"])
        self.assertEqual(impact["research_quality_delta"], "unchanged_but_better_bounded")
        self.assertEqual(impact["pending_created"], 0)


if __name__ == "__main__":
    unittest.main()
