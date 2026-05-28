import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "verification", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase40_research_review_workbench_packet import build_payload
from phase39_helpers import make_phase39_conn


class Phase40ResearchReviewWorkbenchPacketTests(unittest.TestCase):
    def test_workbench_packet_exposes_checklist_and_boundaries(self):
        payload = build_payload(make_phase39_conn(), "300308.SZ")
        packet = payload["research_review_workbench_packet"]
        self.assertEqual(packet["review_candidate_status"], "research_review_candidate")
        self.assertGreater(len(packet["human_checklist"]), 0)
        self.assertGreater(len(packet["why_not_pending"]), 0)
        self.assertIn("request_deeper_research", packet["allowed_review_actions"])
        self.assertIn("Do not create paper order", packet["explicit_non_goals"])
        self.assertFalse(packet["promotion_boundary"]["pending_allowed"])
        self.assertNotIn("target price", json.dumps(payload, ensure_ascii=False).lower())


if __name__ == "__main__":
    unittest.main()
