import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase35_single_stock_thesis import build_payload, render_markdown
from phase34_helpers import make_phase34_conn


class Phase35SingleStockThesisTests(unittest.TestCase):
    def test_thesis_is_conservative_and_not_investment_advice(self):
        payload = build_payload(make_phase34_conn(), ticker="300394.SZ")
        thesis = payload["research_thesis"]
        self.assertEqual(thesis["thesis_confidence"], "medium_low")
        self.assertFalse(thesis["promotion_boundary"]["promotion_allowed"])
        text = json.dumps(payload, ensure_ascii=False).lower() + render_markdown(payload).lower()
        self.assertNotIn("buy recommendation", text)
        self.assertNotIn("sell recommendation", text)
        self.assertIn("supplier share", text)
        self.assertIn("asp", text)


if __name__ == "__main__":
    unittest.main()
