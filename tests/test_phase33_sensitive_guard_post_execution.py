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
from validate_phase33_sensitive_guard_post_execution import build_payload


class Phase33SensitiveGuardPostExecutionTests(unittest.TestCase):
    def test_sensitive_guard_has_no_confirmed_variable_additions(self):
        conn = make_conn_with_candidate(phase31_candidate("ev_sensitive", variable_type="customer_allocation_signal"))
        execute_payload(conn, limit=1, execute=True)
        payload = build_payload(conn)
        self.assertEqual(payload["overall_status"], "pass")
        self.assertEqual(payload["summary"]["confirmed_supplier_share_added"], 0)
        self.assertEqual(payload["summary"]["confirmed_ASP_added"], 0)
        self.assertEqual(payload["summary"]["confirmed_customer_allocation_added"], 0)
        self.assertEqual(payload["summary"]["violations"], 0)


if __name__ == "__main__":
    unittest.main()
