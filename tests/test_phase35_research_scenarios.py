import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase35_research_scenarios import build_payload, render_markdown
from phase34_helpers import make_phase34_conn


class Phase35ResearchScenariosTests(unittest.TestCase):
    def test_scenarios_are_research_only_without_price_or_position(self):
        payload = build_payload(make_phase34_conn(), ticker="300394.SZ")
        text = json.dumps(payload, ensure_ascii=False).lower() + render_markdown(payload).lower()
        self.assertIn("bull_case", text)
        self.assertNotIn("target price", text)
        self.assertNotIn("position size", text)
        self.assertFalse(payload["safety"]["trade_recommendation_generated"])


if __name__ == "__main__":
    unittest.main()
