import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
JOBS_DIR = ROOT / "08_scripts" / "jobs"
VERIFICATION_DIR = ROOT / "08_scripts" / "verification"
TEST_DIR = ROOT / "tests"
for path in (LIB_DIR, JOBS_DIR, VERIFICATION_DIR, TEST_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from execute_phase33_controlled_review_actions import build_payload as execute_payload
from phase31_helpers import make_conn_with_candidate, phase31_candidate
from validate_phase33_post_review_research_impact import build_payload


class Phase33PostReviewResearchImpactTests(unittest.TestCase):
    def test_research_impact_does_not_upgrade_promotion_or_pending(self):
        conn = make_conn_with_candidate(phase31_candidate("ev_sensitive", variable_type="customer_allocation_signal"))
        execute_payload(conn, limit=1, execute=True)
        payload = build_payload(conn)
        self.assertIn(payload["overall_status"], {"partial_pass", "pass"})
        self.assertEqual(payload["summary"]["confirmed_variables_added"], 0)
        self.assertEqual(payload["summary"]["new_pending_created"], 0)
        self.assertEqual(payload["summary"]["promotion_allowed_from_reviewed_evidence"], 0)


if __name__ == "__main__":
    unittest.main()
