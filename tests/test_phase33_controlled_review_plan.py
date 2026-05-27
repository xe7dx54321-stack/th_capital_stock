import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
TEST_DIR = ROOT / "tests"
for path in (LIB_DIR, TEST_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from phase31_helpers import make_conn_with_candidate, phase31_candidate
from smr_controlled_review_plan import build_controlled_review_plan
from smr_semantic_evidence_persistence import write_semantic_evidence_candidates


def unique_candidate(evidence_id: str, variable_type: str):
    candidate = phase31_candidate(evidence_id, variable_type=variable_type)
    candidate["source_id"] = f"ir_{evidence_id}"
    candidate["chunk_id"] = f"chunk_{evidence_id}"
    candidate["quoted_span"] = f"quoted span for {evidence_id}"
    candidate["claim_text"] = candidate["quoted_span"]
    return candidate


class Phase33ControlledReviewPlanTests(unittest.TestCase):
    def test_plan_selects_guarded_sample_and_safe_sensitive_action(self):
        conn = make_conn_with_candidate(
            phase31_candidate("ev_sensitive", variable_type="customer_allocation_signal", quality_bucket="weak_but_usable", quality_score=58)
        )
        write_semantic_evidence_candidates(conn, [unique_candidate("ev_plain", "capacity_signal")])
        payload = build_controlled_review_plan(conn, limit=5, include_generated=False)
        self.assertGreaterEqual(payload["summary"]["planned_items"], 1)
        sensitive = [item for item in payload["plan_items"] if item["sensitive_variable"]]
        self.assertTrue(sensitive)
        self.assertTrue(all(item["recommended_action"] != "approve_evidence" for item in sensitive))
        self.assertFalse(payload["safety"]["promotion_allowed_after_action"])


if __name__ == "__main__":
    unittest.main()
