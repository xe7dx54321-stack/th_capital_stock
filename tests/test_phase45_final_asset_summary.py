import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from phase45_helpers import make_phase45_conn
from build_phase45_final_research_asset_summary import build_payload


class Phase45FinalAssetSummaryTests(unittest.TestCase):
    def test_asset_summary_aggregates_phase35_to_44(self):
        payload = build_payload(make_phase45_conn(), "300308.SZ")
        body = payload["final_research_asset_summary"]
        self.assertIn("single_stock_packet", body["research_asset_stages_completed"])
        self.assertIn("manual_candidate_closeout", body["research_asset_stages_completed"])
        self.assertEqual(body["evidence_chain"]["manual_candidates_reviewed"], 3)
        self.assertEqual(body["manual_candidate_results"]["official_consensus_candidate"], "accepted_not_confirmed")
        self.assertIn("official_consensus_confirmed", body["remaining_core_gaps"])


if __name__ == "__main__":
    unittest.main()
