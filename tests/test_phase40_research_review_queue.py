import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase40_research_review_queue import build_payload
from phase39_helpers import make_phase39_conn


class Phase40ResearchReviewQueueTests(unittest.TestCase):
    def test_300308_enters_queue_and_300394_is_repair_only(self):
        payload = build_payload(make_phase39_conn())
        summary = payload["summary"]
        self.assertEqual(summary["queue_items"], 1)
        self.assertEqual(summary["research_review_candidates"], 1)
        self.assertEqual(summary["repair_required"], 1)
        self.assertEqual(payload["items"][0]["ticker"], "300308.SZ")
        self.assertEqual(payload["repair_rows"][0]["ticker"], "300394.SZ")
        self.assertEqual(summary["pending_allowed_true"], 0)
        self.assertEqual(summary["paper_order_allowed_true"], 0)

    def test_ticker_filter_excludes_repair_row_for_300308(self):
        payload = build_payload(make_phase39_conn(), "300308.SZ")
        self.assertEqual(payload["summary"]["queue_items"], 1)
        self.assertEqual(payload["summary"]["repair_required"], 0)


if __name__ == "__main__":
    unittest.main()
