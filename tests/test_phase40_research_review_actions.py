import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "jobs", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from apply_phase40_research_review_action import build_payload
from phase39_helpers import make_phase39_conn
from smr_research_review_actions import apply_research_review_action
from smr_research_review_audit import list_audit_records
from smr_specific_evidence_request import list_specific_evidence_requests


class Phase40ResearchReviewActionsTests(unittest.TestCase):
    def test_request_deeper_research_dry_run_writes_nothing(self):
        conn = make_phase39_conn()
        payload = build_payload(conn, ticker="300308.SZ", action="request_deeper_research", mode="dry_run")
        result = payload["action_result"]
        self.assertEqual(result["after_status"], "reviewed_request_deeper_research")
        self.assertTrue(result["would_write_audit"])
        self.assertFalse(result["audit_written"])
        self.assertFalse(result["pending_created"])
        self.assertEqual(len(list_audit_records(conn)), 0)

    def test_request_deeper_research_execute_writes_audit_without_pending(self):
        conn = make_phase39_conn()
        payload = build_payload(conn, ticker="300308.SZ", action="request_deeper_research", mode="execute")
        result = payload["action_result"]
        self.assertTrue(result["audit_written"])
        self.assertFalse(result["pending_created"])
        audits = list_audit_records(conn)
        self.assertEqual(len(audits), 1)
        self.assertEqual(audits[0]["before_status"], "research_review_candidate")
        self.assertEqual(audits[0]["after_status"], "reviewed_request_deeper_research")

    def test_request_specific_evidence_creates_request_only_on_execute(self):
        conn = make_phase39_conn()
        build_payload(
            conn,
            ticker="300308.SZ",
            action="request_specific_evidence",
            evidence_type="official_consensus",
            mode="execute",
        )
        requests = list_specific_evidence_requests(conn, ticker="300308.SZ")
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0]["evidence_type"], "official_consensus")
        self.assertEqual(requests[0]["allowed_source_route"], "authorized_source_required")

    def test_forbidden_action_is_intercepted(self):
        with self.assertRaises(ValueError):
            apply_research_review_action(make_phase39_conn(), ticker="300308.SZ", action="approve_pending", mode="execute")


if __name__ == "__main__":
    unittest.main()
