import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
REPORTING_DIR = ROOT / "08_scripts" / "reporting"
TEST_DIR = ROOT / "tests"
for path in (LIB_DIR, REPORTING_DIR, TEST_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase31_evidence_governance_dashboard import build_payload, render_markdown
from phase31_helpers import make_conn_with_candidate, phase31_candidate


class Phase31EvidenceGovernanceDashboardTests(unittest.TestCase):
    def test_dashboard_json_and_markdown(self):
        conn = make_conn_with_candidate(phase31_candidate(variable_type="customer_allocation_signal"))
        payload = build_payload(conn)
        self.assertIn("summary", payload)
        self.assertEqual(payload["summary"]["promotion_allowed_true"], 0)
        self.assertIn("Phase 31 Evidence Governance Dashboard", render_markdown(payload))


if __name__ == "__main__":
    unittest.main()
