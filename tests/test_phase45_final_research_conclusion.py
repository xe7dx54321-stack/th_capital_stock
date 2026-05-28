import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from phase45_helpers import make_phase45_conn
from build_phase45_final_research_conclusion import build_payload, render_markdown


class Phase45FinalResearchConclusionTests(unittest.TestCase):
    def test_final_conclusion_is_watchlist_not_pending_or_trade_advice(self):
        payload = build_payload(make_phase45_conn(), "300308.SZ")
        body = payload["final_research_conclusion"]
        self.assertEqual(body["paper_watchlist_readiness"], "paper_watchlist_candidate")
        self.assertEqual(body["allowed_next_step"], "paper_watchlist_tracking_only")
        self.assertIn("pending_human_review", body["forbidden_next_steps"])
        self.assertEqual(body["pending_created"], 0)
        markdown = render_markdown(payload).lower()
        self.assertNotIn("buy", markdown)
        self.assertNotIn("sell", markdown)


if __name__ == "__main__":
    unittest.main()
