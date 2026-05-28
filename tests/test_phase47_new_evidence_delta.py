import unittest

from phase47_helpers import make_phase47_conn
from build_phase47_new_evidence_delta import build_payload


class Phase47NewEvidenceDeltaTests(unittest.TestCase):
    def test_delta_reports_no_new_evidence(self):
        conn = make_phase47_conn()
        payload = build_payload(conn, "300308.SZ")
        delta = payload["new_evidence_delta"]
        self.assertEqual(delta["delta_status"], "no_new_evidence")
        self.assertFalse(delta["revalidation_required"])
        self.assertFalse(delta["new_evidence_found"])

    def test_delta_has_safety_gates(self):
        conn = make_phase47_conn()
        payload = build_payload(conn, "300308.SZ")
        safety = payload["safety"]
        self.assertTrue(safety["delta_does_not_fetch_raw"])
        self.assertTrue(safety["delta_does_not_pending"])
        self.assertEqual(safety["pending_created"], 0)

    def test_delta_counts_evidence(self):
        conn = make_phase47_conn()
        payload = build_payload(conn, "300308.SZ")
        delta = payload["new_evidence_delta"]
        self.assertIsInstance(delta["evidence_count_before"], int)
        self.assertIsInstance(delta["manual_candidates_count"], int)

    def test_no_new_evidence_is_valid_result(self):
        conn = make_phase47_conn()
        payload = build_payload(conn, "300308.SZ")
        self.assertEqual(
            payload["new_evidence_delta"]["delta_status"],
            "no_new_evidence",
        )

    def test_markdown_output(self):
        from build_phase47_new_evidence_delta import render_markdown
        conn = make_phase47_conn()
        payload = build_payload(conn, "300308.SZ")
        md = render_markdown(payload)
        self.assertIn("New Evidence Delta", md)


if __name__ == "__main__":
    unittest.main()
