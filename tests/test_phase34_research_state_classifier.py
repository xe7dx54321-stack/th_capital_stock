import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase34_research_state_classification import build_payload
from phase34_helpers import make_phase34_conn


class Phase34ResearchStateClassifierTests(unittest.TestCase):
    def test_research_state_is_not_promotion_status(self):
        payload = build_payload(make_phase34_conn(), ticker="300394.SZ")
        row = payload["ticker_results"][0]
        self.assertIn(row["research_state"], {"research_weakened", "unchanged_needs_more_data", "research_strengthened", "ready_for_research_packet"})
        self.assertFalse(row["promotion_status"]["promotion_allowed"])
        self.assertEqual(payload["summary"]["new_pending_created"], 0)


if __name__ == "__main__":
    unittest.main()
