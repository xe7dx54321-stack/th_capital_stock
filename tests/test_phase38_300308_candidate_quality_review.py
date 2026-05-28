import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase38_300308_candidate_quality_review import build_payload
from phase38_helpers import make_phase38_conn


class Phase38300308CandidateQualityReviewTests(unittest.TestCase):
    def test_quality_review_keeps_sensitive_and_product_mix_boundaries(self):
        payload = build_payload(make_phase38_conn())
        review = payload["candidate_quality_review"]
        self.assertEqual(review["candidates_reviewed"], 15)
        self.assertLessEqual(review["eligible_for_persistence"], review["candidates_reviewed"])
        self.assertEqual(review["usable_for_promotion_true"], 0)
        rows = review["quality_rows"]
        self.assertTrue(any(row["variable"] == "product_mix" for row in rows))
        self.assertTrue(all(row["usable_for_promotion"] is False for row in rows))
        customer_rows = [row for row in rows if row["variable"] == "customer_allocation_proxy"]
        self.assertTrue(customer_rows)
        self.assertTrue(all(row["recommended_action"] != "persist_candidate" for row in customer_rows))
        self.assertFalse(payload["safety"]["product_mix_auto_converted_to_asp"])
        self.assertFalse(payload["safety"]["customer_allocation_confirmed"])


if __name__ == "__main__":
    unittest.main()
