import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "jobs", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from execute_phase41_specific_evidence_requests import build_payload
from phase40_helpers import make_phase40_conn_with_action
from smr_research_followup_audit import list_followup_audit_records
from smr_specific_evidence_request import list_specific_evidence_requests


class Phase41SpecificEvidenceRequestExecuteTests(unittest.TestCase):
    def test_dry_run_writes_nothing(self):
        conn = make_phase40_conn_with_action()
        payload = build_payload(conn, ticker="300308.SZ", mode="dry_run")
        body = payload["specific_evidence_request_execution"]
        self.assertEqual(body["requests_planned"], 3)
        self.assertEqual(body["requests_written"], 0)
        self.assertEqual(len(list_specific_evidence_requests(conn, ticker="300308.SZ")), 0)

    def test_execute_writes_three_requests_and_audits_without_pending(self):
        conn = make_phase40_conn_with_action()
        payload = build_payload(conn, ticker="300308.SZ", mode="execute")
        body = payload["specific_evidence_request_execution"]
        self.assertEqual(body["requests_written"], 3)
        self.assertEqual(body["audit_records_written"], 3)
        self.assertEqual(body["pending_created"], 0)
        self.assertEqual(body["paper_order_created"], 0)
        self.assertEqual({row["evidence_type"] for row in list_specific_evidence_requests(conn, ticker="300308.SZ")}, {
            "official_consensus",
            "supplier_share",
            "confirmed_customer_allocation",
        })
        self.assertEqual(len(list_followup_audit_records(conn, ticker="300308.SZ")), 3)

    def test_single_official_consensus_execute_is_request_not_confirmation(self):
        conn = make_phase40_conn_with_action()
        payload = build_payload(conn, ticker="300308.SZ", evidence_type="official_consensus", mode="execute")
        body = payload["specific_evidence_request_execution"]
        self.assertEqual(body["requests_written"], 1)
        self.assertFalse(payload["safety"]["official_consensus_confirmed"])
        request = list_specific_evidence_requests(conn, ticker="300308.SZ")[0]
        self.assertEqual(request["allowed_source_route"], "authorized_source_required")


if __name__ == "__main__":
    unittest.main()
