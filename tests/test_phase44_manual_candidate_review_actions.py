import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "jobs", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from apply_phase44_manual_candidate_review_action import build_payload
from phase43_helpers import make_phase43_conn_with_persisted
from smr_manual_candidate_review_lifecycle import list_lifecycles


class Phase44ManualCandidateReviewActionTests(unittest.TestCase):
    def test_dry_run_and_execute_keep_accept_not_confirmed(self):
        conn = make_phase43_conn_with_persisted()
        dry = build_payload(conn, ticker="300308.SZ", candidate_type="official_consensus", action="accept_as_candidate", mode="dry_run")
        self.assertFalse(dry["manual_candidate_review_action"]["audit_written"])
        self.assertEqual(len(list_lifecycles(conn, "300308.SZ")), 0)

        executed = build_payload(conn, ticker="300308.SZ", candidate_type="official_consensus", action="accept_as_candidate", mode="execute")
        body = executed["manual_candidate_review_action"]
        self.assertTrue(body["audit_written"])
        self.assertEqual(body["after_status"], "manual_candidate_accepted")
        self.assertEqual(body["confirmation_status"], "candidate_not_confirmed")
        self.assertFalse(body["usable_for_promotion"])

    def test_supplier_and_customer_default_review_actions(self):
        conn = make_phase43_conn_with_persisted()
        supplier = build_payload(conn, ticker="300308.SZ", candidate_type="supplier_share", action="mark_as_scenario_only", mode="execute")
        customer = build_payload(conn, ticker="300308.SZ", candidate_type="customer_allocation", action="mark_as_proxy_only", mode="execute")
        self.assertEqual(supplier["manual_candidate_review_action"]["after_status"], "manual_candidate_scenario_only")
        self.assertEqual(customer["manual_candidate_review_action"]["after_status"], "manual_candidate_proxy_only")

    def test_forbidden_action_is_intercepted(self):
        payload = build_payload(
            make_phase43_conn_with_persisted(),
            ticker="300308.SZ",
            candidate_type="official_consensus",
            action="allow_promotion",
            mode="execute",
        )
        body = payload["manual_candidate_review_action"]
        self.assertFalse(body["action_allowed"])
        self.assertEqual(body["blocked_reason"], "forbidden_manual_candidate_review_action")
        self.assertTrue(payload["safety"]["forbidden_action_intercepted"])


if __name__ == "__main__":
    unittest.main()
