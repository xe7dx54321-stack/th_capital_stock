import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "verification", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase44_manual_candidate_closeout_packet import build_payload
from phase44_helpers import make_phase44_closeout_conn


class Phase44CloseoutPacketTests(unittest.TestCase):
    def test_closeout_packet_closes_branch_and_points_to_phase45(self):
        payload = build_payload(make_phase44_closeout_conn(), "300308.SZ")
        body = payload["manual_candidate_closeout_packet"]
        self.assertEqual(body["manual_candidates_reviewed"], 3)
        self.assertGreaterEqual(body["audit_records"], 3)
        self.assertEqual(body["manual_intake_branch_status"], "closed")
        self.assertEqual(body["next_mainline_step"], "phase45_final_research_packet_review")
        self.assertEqual(body["research_impact"]["pending_created"], 0)


if __name__ == "__main__":
    unittest.main()
