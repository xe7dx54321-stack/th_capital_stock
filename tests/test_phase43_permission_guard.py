import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase43_manual_intake_permission_audit import build_payload
from phase43_helpers import make_phase43_conn_with_candidates


class Phase43PermissionGuardTests(unittest.TestCase):
    def test_permission_guard_downgrades_scenario_and_proxy_usage(self):
        payload = build_payload(make_phase43_conn_with_candidates(), "300308.SZ")
        body = payload["permission_audit"]
        self.assertEqual(body["manual_candidates_checked"], 3)
        self.assertEqual(body["permission_passed"], 3)
        self.assertEqual(body["permission_blocked"], 0)
        self.assertEqual(body["allowed_usage_downgraded"], 2)
        rows = {row["evidence_type"]: row for row in body["audit_rows"]}
        self.assertEqual(rows["supplier_share"]["final_allowed_usage"], "scenario_analysis_only")
        self.assertEqual(rows["confirmed_customer_allocation"]["final_allowed_usage"], "bear_case_context_or_scenario_support")
        self.assertEqual(body["promotion_allowed_true"], 0)


if __name__ == "__main__":
    unittest.main()
