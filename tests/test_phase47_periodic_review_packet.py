import unittest

from phase47_helpers import make_phase47_active_conn
from build_phase47_periodic_review_packet import build_payload


class Phase47PeriodicReviewPacketTests(unittest.TestCase):
    def test_packet_has_required_sections(self):
        conn = make_phase47_active_conn()
        payload = build_payload(conn, "300308.SZ")
        packet = payload["periodic_review_packet"]
        self.assertIn("watchlist_status", packet)
        self.assertIn("review_status", packet)
        self.assertIn("tracking_variable_snapshot", packet)
        self.assertIn("new_evidence_delta", packet)
        self.assertIn("thesis_strength_update", packet)
        self.assertIn("review_judgment", packet)

    def test_why_not_pending(self):
        conn = make_phase47_active_conn()
        payload = build_payload(conn, "300308.SZ")
        reasons = payload["periodic_review_packet"]["why_not_pending"]
        self.assertIn("official consensus remains unconfirmed", reasons)
        self.assertIn("supplier share remains scenario-only", reasons)
        self.assertIn("customer allocation remains proxy-only", reasons)

    def test_forbidden_actions(self):
        conn = make_phase47_active_conn()
        payload = build_payload(conn, "300308.SZ")
        forbidden = payload["periodic_review_packet"]["forbidden_actions"]
        self.assertIn("create_pending", forbidden)
        self.assertIn("create_paper_order", forbidden)
        self.assertIn("create_trade", forbidden)

    def test_judgment_continue_tracking(self):
        conn = make_phase47_active_conn()
        payload = build_payload(conn, "300308.SZ")
        judgment = payload["periodic_review_packet"]["review_judgment"]
        self.assertTrue(judgment["continue_tracking"])
        self.assertFalse(judgment["archive_candidate"])

    def test_safety_gates(self):
        conn = make_phase47_active_conn()
        payload = build_payload(conn, "300308.SZ")
        safety = payload["safety"]
        self.assertFalse(safety["packet_strengthened_is_buy"])
        self.assertFalse(safety["packet_creates_pending"])
        self.assertFalse(safety["packet_creates_order"])
        self.assertFalse(safety["packet_creates_trade"])

    def test_markdown_output(self):
        from build_phase47_periodic_review_packet import render_markdown
        conn = make_phase47_active_conn()
        payload = build_payload(conn, "300308.SZ")
        md = render_markdown(payload)
        self.assertIn("Periodic Review Packet", md)
        self.assertIn("Why Not Pending", md)
        self.assertIn("Forbidden Actions", md)


if __name__ == "__main__":
    unittest.main()
