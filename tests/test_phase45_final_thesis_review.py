import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from phase45_helpers import make_phase45_conn
from build_phase45_final_thesis_review import build_payload, render_markdown


class Phase45FinalThesisReviewTests(unittest.TestCase):
    def test_thesis_review_separates_research_from_investment(self):
        payload = build_payload(make_phase45_conn(), "300308.SZ")
        body = payload["final_thesis_review"]
        self.assertEqual(body["conclusion_readiness"], "formal_research_conclusion_possible")
        self.assertEqual(body["investment_readiness"], "not_ready")
        self.assertNotEqual(body["thesis_confidence"], "high")
        markdown = render_markdown(payload).lower()
        self.assertNotIn("buy", markdown)
        self.assertNotIn("sell", markdown)


if __name__ == "__main__":
    unittest.main()
