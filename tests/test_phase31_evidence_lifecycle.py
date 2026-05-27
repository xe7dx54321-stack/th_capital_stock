import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
TEST_DIR = ROOT / "tests"
for path in (LIB_DIR, TEST_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from phase31_helpers import phase31_candidate
from smr_evidence_lifecycle import (
    lifecycle_from_candidate,
    validate_lifecycle_object,
    validate_status_transition,
)


class Phase31EvidenceLifecycleTests(unittest.TestCase):
    def test_lifecycle_defaults_promotion_false(self):
        item = lifecycle_from_candidate(phase31_candidate())
        self.assertEqual(item["lifecycle_status"], "persisted_candidate")
        self.assertFalse(item["usable_for_promotion"])
        self.assertEqual(validate_lifecycle_object(item), [])

    def test_review_required_candidate_enters_pending_review(self):
        item = lifecycle_from_candidate(phase31_candidate(quality_bucket="weak_but_usable", quality_score=58))
        self.assertEqual(item["lifecycle_status"], "pending_review")
        self.assertEqual(item["review_status"], "review_required")

    def test_status_transition_validation(self):
        ok, _ = validate_status_transition("persisted_candidate", "approved_evidence")
        self.assertTrue(ok)
        ok, _ = validate_status_transition("archived", "approved_evidence")
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
