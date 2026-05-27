import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
REPORTING_DIR = ROOT / "08_scripts" / "reporting"
TEST_DIR = ROOT / "tests"
for path in (LIB_DIR, REPORTING_DIR, TEST_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase32_priority_review_packet import build_payload, render_markdown
from phase31_helpers import make_conn_with_candidate, phase31_candidate


class Phase32PriorityReviewPacketTests(unittest.TestCase):
    def test_priority_packet_json_markdown_and_dry_run_command(self):
        conn = make_conn_with_candidate(phase31_candidate(variable_type="customer_allocation_signal", quality_bucket="weak_but_usable", quality_score=58))
        payload = build_payload(conn, ticker="300394.SZ", priority="high")
        self.assertGreaterEqual(payload["summary"]["packet_items"], 1)
        item = payload["items"][0]
        self.assertIn("--dry-run --json", item["action_command_dry_run"])
        self.assertNotIn("--execute", item["action_command_dry_run"])
        md = render_markdown(payload)
        self.assertIn("Phase 32 Priority Evidence Review Packet", md)
        self.assertIn("Blocked actions", md)


if __name__ == "__main__":
    unittest.main()
