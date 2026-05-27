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

from phase31_helpers import make_conn_with_candidate, phase31_candidate
from smr_sensitive_variable_guard import guard_sensitive_variable
from validate_phase31_sensitive_variable_guard import build_payload


class Phase31SensitiveVariableGuardTests(unittest.TestCase):
    def test_confirmed_sensitive_upgrade_blocked(self):
        result = guard_sensitive_variable(
            {"evidence_id": "ev", "variable_type": "supplier_share", "evidence_status": "confirmed", "allowed_usage": "research_evidence"},
            action="upgrade_to_confirmed_supplier_share",
        )
        self.assertTrue(result["blocked_confirmed_upgrade"])
        self.assertTrue(result["violations"])

    def test_validator_reports_no_live_violations(self):
        conn = make_conn_with_candidate(phase31_candidate(variable_type="capacity_signal"))
        payload = build_payload(conn)
        self.assertEqual(payload["overall_status"], "pass")
        self.assertEqual(payload["summary"]["violations"], 0)


if __name__ == "__main__":
    unittest.main()
