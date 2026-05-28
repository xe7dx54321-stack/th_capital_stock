import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "verification", ROOT / "08_scripts" / "reporting", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from validate_phase44_manual_candidate_research_impact_closeout import build_payload
from phase44_helpers import make_phase44_closeout_conn


class Phase44ResearchImpactCloseoutTests(unittest.TestCase):
    def test_closeout_impact_does_not_create_pending(self):
        payload = build_payload(make_phase44_closeout_conn(), "300308.SZ")
        self.assertEqual(payload["overall_status"], "pass")
        impact = payload["manual_candidate_research_impact_closeout"]
        self.assertEqual(impact["manual_candidates_reviewed"], 3)
        self.assertTrue(impact["official_consensus_candidate_accepted"])
        self.assertTrue(impact["supplier_share_scenario_only"])
        self.assertTrue(impact["customer_allocation_proxy_only"])
        self.assertFalse(impact["official_consensus_confirmed"])
        self.assertEqual(impact["pending_created"], 0)


if __name__ == "__main__":
    unittest.main()
