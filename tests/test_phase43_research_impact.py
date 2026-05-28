import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "verification", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from validate_phase43_manual_intake_research_impact import build_payload
from phase43_helpers import make_phase43_conn_with_persisted


class Phase43ResearchImpactTests(unittest.TestCase):
    def test_manual_candidates_improve_context_without_confirming_variables(self):
        payload = build_payload(make_phase43_conn_with_persisted(), "300308.SZ")
        self.assertEqual(payload["overall_status"], "pass")
        impact = payload["manual_intake_research_impact"]
        self.assertEqual(impact["manual_candidates_written"], 3)
        self.assertTrue(impact["official_consensus_candidate_added"])
        self.assertFalse(impact["official_consensus_confirmed"])
        self.assertFalse(impact["supplier_share_confirmed"])
        self.assertFalse(impact["customer_allocation_confirmed"])
        self.assertEqual(impact["pending_created"], 0)


if __name__ == "__main__":
    unittest.main()
