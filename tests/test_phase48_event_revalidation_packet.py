import unittest
from phase48_helpers import make_phase48_active_conn
from build_phase48_event_revalidation_packet import build_payload

class Phase48EventRevalidationPacketTests(unittest.TestCase):
    def test_packet_sections(self):
        conn = make_phase48_active_conn()
        p = build_payload(conn, "300308.SZ")
        pkt = p["event_revalidation_packet"]
        self.assertIn("events_detected", pkt)
        self.assertIn("tracking_variable_refresh", pkt)
        self.assertIn("thesis_strength_update", pkt)
        self.assertIn("review_judgment", pkt)
    def test_why_not_pending(self):
        conn = make_phase48_active_conn()
        p = build_payload(conn, "300308.SZ")
        reasons = p["event_revalidation_packet"]["why_not_pending"]
        self.assertIn("official consensus remains unconfirmed", reasons)
    def test_forbidden_actions(self):
        conn = make_phase48_active_conn()
        p = build_payload(conn, "300308.SZ")
        fa = p["event_revalidation_packet"]["forbidden_actions"]
        self.assertIn("create_pending", fa)
        self.assertIn("create_trade", fa)
    def test_continue_tracking(self):
        conn = make_phase48_active_conn()
        p = build_payload(conn, "300308.SZ")
        j = p["event_revalidation_packet"]["review_judgment"]
        self.assertTrue(j["continue_tracking"])
        self.assertFalse(j["archive_candidate"])
    def test_no_trade_output(self):
        conn = make_phase48_active_conn()
        p = build_payload(conn, "300308.SZ")
        s = p["safety"]
        self.assertFalse(s["packet_creates_pending"])
        self.assertFalse(s["packet_creates_order"])
        self.assertFalse(s["packet_creates_trade"])
if __name__ == "__main__": unittest.main()
