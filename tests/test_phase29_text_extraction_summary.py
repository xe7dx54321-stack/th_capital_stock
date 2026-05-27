import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
REPORTING_DIR = ROOT / "08_scripts" / "reporting"
for path in (LIB_DIR, REPORTING_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase29_text_extraction_summary import build_payload, render_markdown


class Phase29TextExtractionSummaryTests(unittest.TestCase):
    def test_summary_json_and_markdown(self):
        conn = sqlite3.connect(":memory:")
        payload = build_payload(conn, tickers="300394.SZ")
        self.assertIn("summary", payload)
        md = render_markdown(payload)
        self.assertIn("Phase 29 Real IR Document Text Extraction Summary", md)
        self.assertIn("Extraction Failures", md)


if __name__ == "__main__":
    unittest.main()
