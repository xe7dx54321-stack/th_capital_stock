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

from test_phase25_end_demand_proxy import make_evidence_conn
from validate_phase25_expectation_gap_gate_integration import build_payload


class Phase25GateIntegrationTests(unittest.TestCase):
    def test_expectation_gap_alone_does_not_create_pending(self):
        payload = build_payload(make_evidence_conn(), tickers="300394.SZ,300308.SZ")
        self.assertEqual(payload["summary"]["new_pending_created"], 0)
        self.assertEqual(payload["summary"]["promotion_allowed_from_gap_only"], 0)
        self.assertFalse(payload["safety"]["promotion_rules_relaxed"])
        self.assertFalse(payload["ticker_results"][0]["gate_impact"]["promotion_allowed"])


if __name__ == "__main__":
    unittest.main()
