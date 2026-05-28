import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from phase43_helpers import make_phase43_conn_with_persisted
from smr_manual_candidate_review_lifecycle import lifecycle_from_candidate, list_lifecycles, load_or_build_candidate, upsert_lifecycle, validate_transition


class Phase44ManualCandidateLifecycleTests(unittest.TestCase):
    def test_accepted_candidate_lifecycle_is_not_confirmed(self):
        conn = make_phase43_conn_with_persisted()
        candidate = load_or_build_candidate(conn, ticker="300308.SZ", candidate_type="official_consensus")
        lifecycle = lifecycle_from_candidate(candidate, status="manual_candidate_accepted", action="accept_as_candidate")
        updated = upsert_lifecycle(conn, lifecycle)
        self.assertEqual(updated["status"], "manual_candidate_accepted")
        self.assertEqual(updated["confirmation_status"], "candidate_not_confirmed")
        self.assertFalse(updated["usable_for_promotion"])
        self.assertFalse(updated["pending_allowed"])
        self.assertEqual(len(list_lifecycles(conn, "300308.SZ")), 1)

    def test_status_transition_blocks_reopening_archived(self):
        ok, reason = validate_transition("manual_candidate_archived", "manual_candidate_accepted")
        self.assertFalse(ok)
        self.assertIn("archived", reason)


if __name__ == "__main__":
    unittest.main()
