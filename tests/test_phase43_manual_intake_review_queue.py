import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase43_manual_intake_review_queue import build_payload
from phase43_helpers import make_phase43_conn_with_candidates


class Phase43ManualIntakeReviewQueueTests(unittest.TestCase):
    def test_review_queue_includes_three_candidates_and_forbidden_actions(self):
        payload = build_payload(make_phase43_conn_with_candidates(), "300308.SZ")
        body = payload["manual_intake_review_queue"]
        self.assertEqual(body["queue_items"], 3)
        self.assertEqual(body["official_consensus_candidates"], 1)
        self.assertEqual(body["scenario_candidates"], 1)
        self.assertEqual(body["proxy_candidates"], 1)
        for item in body["items"]:
            self.assertIn("create_pending", item["forbidden_actions"])
            self.assertIn("allow_promotion", item["forbidden_actions"])
            self.assertIn("not_confirmed", item["review_reason"])


if __name__ == "__main__":
    unittest.main()
