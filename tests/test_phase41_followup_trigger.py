import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase41_followup_trigger_summary import build_payload
from phase40_helpers import make_phase40_conn_with_action


class Phase41FollowupTriggerTests(unittest.TestCase):
    def test_300308_trigger_detected_and_300394_excluded(self):
        payload = build_payload(make_phase40_conn_with_action())
        self.assertEqual(payload["summary"]["followup_triggers_found"], 1)
        self.assertEqual(payload["summary"]["request_deeper_research"], 1)
        self.assertEqual(payload["summary"]["repair_required_excluded"], 1)
        self.assertEqual(payload["trigger_rows"][0]["ticker"], "300308.SZ")
        self.assertEqual(payload["trigger_rows"][0]["trigger_status"], "active")
        self.assertEqual(payload["excluded_rows"][0]["ticker"], "300394.SZ")


if __name__ == "__main__":
    unittest.main()
