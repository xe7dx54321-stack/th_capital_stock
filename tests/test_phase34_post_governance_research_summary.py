import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase34_post_governance_research_summary import build_payload, render_markdown
from phase34_helpers import make_phase34_conn


class Phase34PostGovernanceResearchSummaryTests(unittest.TestCase):
    def test_summary_json_and_markdown_keep_safety_boundaries(self):
        payload = build_payload(make_phase34_conn(), ticker="300394.SZ")
        self.assertEqual(payload["summary"]["new_pending_created"], 0)
        self.assertEqual(payload["summary"]["paper_order_created"], 0)
        self.assertEqual(len(payload["ticker_rows"]), 1)
        markdown = render_markdown(payload)
        self.assertIn("Phase 34 Post-Governance Research Revalidation Summary", markdown)
        self.assertIn("300394.SZ", markdown)


if __name__ == "__main__":
    unittest.main()
