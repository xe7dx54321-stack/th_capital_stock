import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
VERIFICATION_DIR = ROOT / "08_scripts" / "verification"
TEST_DIR = ROOT / "tests"
for path in (LIB_DIR, VERIFICATION_DIR, TEST_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from phase31_helpers import make_conn_with_candidate
from validate_phase31_evidence_governance_revalidation import build_payload


class Phase31EvidenceGovernanceRevalidationTests(unittest.TestCase):
    def test_revalidation_has_no_pending_or_paper_order(self):
        conn = make_conn_with_candidate()
        payload = build_payload(conn)
        self.assertEqual(payload["overall_status"], "pass")
        self.assertEqual(payload["summary"]["new_pending_created"], 0)
        self.assertEqual(payload["summary"]["paper_order_created"], 0)
        self.assertEqual(payload["summary"]["promotion_allowed_true"], 0)


if __name__ == "__main__":
    unittest.main()
