import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase41_research_followup_queue import build_payload
from phase41_helpers import make_phase41_conn_with_followups


class Phase41ResearchFollowupQueueTests(unittest.TestCase):
    def test_followup_queue_has_three_core_gap_items(self):
        payload = build_payload(make_phase41_conn_with_followups(), "300308.SZ")
        summary = payload["summary"]
        self.assertEqual(summary["followup_queue_items"], 3)
        self.assertEqual(summary["official_consensus_requests"], 1)
        self.assertEqual(summary["supplier_share_requests"], 1)
        self.assertEqual(summary["customer_allocation_requests"], 1)
        self.assertEqual(summary["pending_created"], 0)
        self.assertTrue(all(item["do_not_do"] for item in payload["items"]))


if __name__ == "__main__":
    unittest.main()
