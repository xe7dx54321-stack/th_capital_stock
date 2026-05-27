import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
VERIFICATION_DIR = ROOT / "08_scripts" / "verification"
for path in (LIB_DIR, VERIFICATION_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from validate_phase29_text_extraction_semantic_evidence import build_payload


class Phase29TextExtractionRevalidationTests(unittest.TestCase):
    def test_revalidation_runs_without_pending(self):
        conn = sqlite3.connect(":memory:")
        payload = build_payload(conn, tickers="300394.SZ")
        self.assertEqual(payload["overall_status"], "partial_pass")
        self.assertEqual(payload["summary"]["new_pending_created"], 0)
        self.assertEqual(payload["summary"]["promotion_allowed_from_semantic_evidence_only"], 0)


if __name__ == "__main__":
    unittest.main()
