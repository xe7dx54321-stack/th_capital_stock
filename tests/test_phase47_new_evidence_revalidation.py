import unittest

from phase47_helpers import make_phase47_conn
from validate_phase47_new_evidence_revalidation import build_payload


class Phase47NewEvidenceRevalidationTests(unittest.TestCase):
    def test_noop_when_no_new_evidence(self):
        conn = make_phase47_conn()
        payload = build_payload(conn, "300308.SZ")
        rev = payload["new_evidence_revalidation"]
        self.assertFalse(rev["revalidation_required"])
        self.assertEqual(rev["overall_status"], "no_new_evidence_noop")
        self.assertEqual(rev["pending_created"], 0)
        self.assertEqual(rev["paper_order_created"], 0)
        self.assertEqual(rev["real_trade_created"], 0)

    def test_safety_gates(self):
        conn = make_phase47_conn()
        payload = build_payload(conn, "300308.SZ")
        safety = payload["safety"]
        self.assertFalse(safety["revalidation_creates_pending"])
        self.assertFalse(safety["revalidation_creates_order"])
        self.assertFalse(safety["revalidation_creates_trade"])

    def test_revalidation_no_pending_order_trade(self):
        conn = make_phase47_conn()
        payload = build_payload(conn, "300308.SZ")
        rev = payload["new_evidence_revalidation"]
        self.assertEqual(rev["pending_created"], 0)
        self.assertEqual(rev["paper_order_created"], 0)
        self.assertEqual(rev["real_trade_created"], 0)


if __name__ == "__main__":
    unittest.main()
