import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "verification", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from phase40_helpers import make_phase40_conn_with_action
from validate_phase40_research_review_post_action import build_payload


class Phase40PostActionRevalidationTests(unittest.TestCase):
    def test_post_action_revalidation_passes_without_forbidden_side_effects(self):
        payload = build_payload(make_phase40_conn_with_action())
        summary = payload["summary"]
        self.assertEqual(payload["overall_status"], "pass")
        self.assertEqual(summary["research_review_actions_executed"], 1)
        self.assertEqual(summary["audit_records_written"], 1)
        self.assertEqual(summary["pending_created"], 0)
        self.assertEqual(summary["paper_order_created"], 0)
        self.assertEqual(summary["forbidden_action_violations"], 0)


if __name__ == "__main__":
    unittest.main()
