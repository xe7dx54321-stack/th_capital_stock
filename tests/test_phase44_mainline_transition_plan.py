import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting",):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase44_mainline_transition_plan import build_payload


class Phase44MainlineTransitionPlanTests(unittest.TestCase):
    def test_transition_plan_closes_governance_branch(self):
        payload = build_payload()
        body = payload["mainline_transition_plan"]
        self.assertEqual(body["branch_status"], "closed_after_phase44")
        self.assertEqual(body["next_phase"], "phase45_final_research_packet_review")
        self.assertIn("more manual candidate governance phases", body["do_not_continue_with"])
        self.assertEqual(body["pending_created"], 0)


if __name__ == "__main__":
    unittest.main()
