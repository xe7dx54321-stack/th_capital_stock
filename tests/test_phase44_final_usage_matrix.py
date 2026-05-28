import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase44_manual_candidate_final_usage_matrix import build_payload
from phase44_helpers import make_phase44_closeout_conn


class Phase44FinalUsageMatrixTests(unittest.TestCase):
    def test_final_usage_matrix_keeps_confirmed_variables_zero(self):
        payload = build_payload(make_phase44_closeout_conn(), "300308.SZ")
        body = payload["manual_candidate_final_usage_matrix"]
        self.assertEqual(body["candidate_count"], 3)
        self.assertEqual(body["confirmed_variables_added"], 0)
        self.assertEqual(body["usable_for_promotion_true"], 0)
        rows = {row["candidate_type"]: row for row in body["rows"]}
        self.assertEqual(rows["official_consensus"]["review_status"], "manual_candidate_accepted")
        self.assertEqual(rows["supplier_share"]["review_status"], "manual_candidate_scenario_only")
        self.assertEqual(rows["customer_allocation"]["review_status"], "manual_candidate_proxy_only")
        self.assertTrue(all(row["final_limitations"] for row in body["rows"]))


if __name__ == "__main__":
    unittest.main()
