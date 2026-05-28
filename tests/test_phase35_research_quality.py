import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase35_research_quality_score import build_payload, render_markdown
from phase34_helpers import make_phase34_conn


class Phase35ResearchQualityTests(unittest.TestCase):
    def test_quality_score_is_not_rating_or_auto_pending(self):
        payload = build_payload(make_phase34_conn(), ticker="300394.SZ")
        quality = payload["research_quality"]
        self.assertNotEqual(quality["overall_quality"], "high")
        self.assertEqual(quality["research_readiness"], "needs_more_data")
        self.assertFalse(payload["safety"]["quality_is_investment_rating"])
        self.assertIn("supplier_share", " ".join(quality["key_quality_gaps"]))
        self.assertIn("Research Quality Score", render_markdown(payload))


if __name__ == "__main__":
    unittest.main()
