import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
JOBS_DIR = ROOT / "08_scripts" / "jobs"
TEST_DIR = ROOT / "tests"
for path in (LIB_DIR, JOBS_DIR, TEST_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from execute_phase33_controlled_review_actions import build_payload
from phase31_helpers import make_conn_with_candidate, phase31_candidate
from smr_evidence_lifecycle import get_lifecycle_state
from smr_evidence_review_audit import list_evidence_review_audits
from smr_semantic_evidence_persistence import write_semantic_evidence_candidates


def unique_candidate(evidence_id: str, variable_type: str):
    candidate = phase31_candidate(evidence_id, variable_type=variable_type)
    candidate["source_id"] = f"ir_{evidence_id}"
    candidate["chunk_id"] = f"chunk_{evidence_id}"
    candidate["quoted_span"] = f"quoted span for {evidence_id}"
    candidate["claim_text"] = candidate["quoted_span"]
    return candidate


class Phase33ControlledReviewExecutorTests(unittest.TestCase):
    def test_dry_run_does_not_write_state(self):
        conn = make_conn_with_candidate(phase31_candidate("ev_plain", variable_type="capacity_signal"))
        payload = build_payload(conn, limit=1, execute=False)
        self.assertEqual(payload["summary"]["actions_executed"], 0)
        self.assertEqual(list_evidence_review_audits(conn), [])
        self.assertIsNone(get_lifecycle_state(conn, "ev_plain"))

    def test_execute_writes_lifecycle_and_audit_without_promotion(self):
        conn = make_conn_with_candidate(phase31_candidate("ev_sensitive", variable_type="customer_allocation_signal", quality_bucket="weak_but_usable", quality_score=58))
        write_semantic_evidence_candidates(conn, [unique_candidate("ev_plain", "capacity_signal")])
        payload = build_payload(conn, limit=2, execute=True)
        self.assertGreater(payload["summary"]["actions_executed"], 0)
        self.assertGreater(payload["summary"]["audit_records_written"], 0)
        self.assertEqual(payload["summary"]["promotion_allowed_after_actions"], 0)
        self.assertEqual(payload["summary"]["new_pending_created"], 0)
        self.assertTrue(list_evidence_review_audits(conn))


if __name__ == "__main__":
    unittest.main()
