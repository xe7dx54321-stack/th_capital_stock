import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase38_300308_targeted_review_queue import build_payload
from phase38_helpers import make_phase38_conn


class Phase38300308TargetedReviewQueueTests(unittest.TestCase):
    def test_review_queue_is_dry_run_only_and_contains_sensitive_items(self):
        payload = build_payload(make_phase38_conn())
        queue = payload["targeted_review_queue"]
        self.assertGreater(queue["queue_items"], 0)
        self.assertGreater(queue["sensitive_variable_items"], 0)
        self.assertTrue(all("--dry-run" in item["dry_run_command"] for item in queue["items"]))
        self.assertFalse(payload["safety"]["execute_command_generated"])
        self.assertFalse(payload["safety"]["sensitive_item_recommends_approve"])


if __name__ == "__main__":
    unittest.main()
