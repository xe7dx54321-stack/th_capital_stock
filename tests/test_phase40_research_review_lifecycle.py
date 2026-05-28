import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from phase39_helpers import make_phase39_conn
from smr_research_review_lifecycle import (
    build_phase39_lifecycle_object,
    set_lifecycle_status,
    upsert_lifecycle,
    validate_status_transition,
)


class Phase40ResearchReviewLifecycleTests(unittest.TestCase):
    def test_lifecycle_schema_creates_research_only_candidate(self):
        conn = make_phase39_conn()
        lifecycle = build_phase39_lifecycle_object(conn, "300308.SZ")
        self.assertEqual(lifecycle["research_review_status"], "research_review_candidate")
        self.assertEqual(lifecycle["review_action_status"], "not_started")
        self.assertFalse(lifecycle["pending_allowed"])
        self.assertFalse(lifecycle["paper_order_allowed"])
        self.assertFalse(lifecycle["promotion_allowed"])

    def test_lifecycle_transition_keeps_promotion_disabled(self):
        conn = make_phase39_conn()
        lifecycle = upsert_lifecycle(conn, build_phase39_lifecycle_object(conn, "300308.SZ"))
        updated = set_lifecycle_status(
            conn,
            review_candidate_id=lifecycle["review_candidate_id"],
            research_review_status="reviewed_request_deeper_research",
            review_action_status="needs_follow_up",
        )
        self.assertEqual(updated["research_review_status"], "reviewed_request_deeper_research")
        self.assertFalse(updated["promotion_allowed"])
        self.assertIsNotNone(updated["last_reviewed_at"])

    def test_lifecycle_rejects_pending_transition(self):
        with self.assertRaises(ValueError):
            validate_status_transition("research_review_candidate", "pending_human_review")


if __name__ == "__main__":
    unittest.main()
