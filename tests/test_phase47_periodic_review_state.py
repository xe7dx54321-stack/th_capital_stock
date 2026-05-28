import unittest

from phase47_helpers import make_phase47_conn
from build_phase47_periodic_review_state import build_payload
from smr_paper_watchlist_periodic_review import (
    REVIEW_STATUSES,
    REVIEW_CADENCES,
    build_periodic_review_state,
)


class Phase47PeriodicReviewStateTests(unittest.TestCase):
    def test_build_state_without_db(self):
        conn = make_phase47_conn()
        state = build_periodic_review_state(conn, "300308.SZ")
        self.assertEqual(state["ticker"], "300308.SZ")
        self.assertEqual(state["review_status"], "review_due")
        self.assertFalse(state["pending_allowed"])
        self.assertFalse(state["paper_order_allowed"])
        self.assertFalse(state["real_trade_allowed"])

    def test_review_statuses_defined(self):
        self.assertIn("review_due", REVIEW_STATUSES)
        self.assertIn("review_completed", REVIEW_STATUSES)
        self.assertIn("review_strengthened", REVIEW_STATUSES)
        self.assertIn("review_weakened", REVIEW_STATUSES)

    def test_review_cadences_defined(self):
        self.assertIn("weekly_or_on_new_evidence", REVIEW_CADENCES)
        self.assertIn("weekly", REVIEW_CADENCES)

    def test_build_payload_reports_review_due(self):
        conn = make_phase47_conn()
        payload = build_payload(conn, "300308.SZ")
        state = payload["periodic_review_state"]
        self.assertEqual(state["ticker"], "300308.SZ")
        self.assertIn(state["review_status"], REVIEW_STATUSES)
        safety = payload["safety"]
        self.assertFalse(safety["review_due_is_pending"])
        self.assertFalse(safety["review_strengthened_is_buy"])

    def test_build_markdown(self):
        from build_phase47_periodic_review_state import render_markdown
        conn = make_phase47_conn()
        payload = build_payload(conn, "300308.SZ")
        md = render_markdown(payload)
        self.assertIn("Periodic Review State", md)
        self.assertIn("300308.SZ", md)


if __name__ == "__main__":
    unittest.main()
