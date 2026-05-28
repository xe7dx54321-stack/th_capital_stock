import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase39_300394_repair_status_summary import build_payload
from phase39_helpers import make_phase39_conn


class Phase39300394RepairStatusTests(unittest.TestCase):
    def test_repair_status_does_not_generate_research_packet(self):
        payload = build_payload(make_phase39_conn())
        body = payload["repair_status_summary"]
        self.assertEqual(body["repair_tasks_total"], 5)
        self.assertEqual(body["current_status"], "repair_required_before_research_deepening")
        self.assertFalse(body["research_deepening_allowed"])
        self.assertIn("TICKER_MAPPING_RECHECK", body["repair_categories"])
        self.assertFalse(payload["safety"]["research_packet_generated"])
        self.assertFalse(payload["safety"]["fake_evidence_written"])


if __name__ == "__main__":
    unittest.main()
