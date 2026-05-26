import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
REPORTING_DIR = ROOT / "08_scripts" / "reporting"
for path in (LIB_DIR, REPORTING_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase27_semantic_evidence_summary import build_payload, render_markdown


class Phase27SemanticEvidenceSummaryTests(unittest.TestCase):
    def test_summary_json_and_markdown(self):
        payload = build_payload(tickers="300394.SZ", mode="mock")
        markdown = render_markdown(payload)
        self.assertEqual(payload["summary"]["tickers_checked"], 1)
        self.assertGreater(payload["summary"]["semantic_extractions"], 0)
        self.assertEqual(payload["summary"]["new_pending_created"], 0)
        self.assertIn("# Phase 27 Semantic Evidence Summary", markdown)


if __name__ == "__main__":
    unittest.main()
