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

from validate_phase27_semantic_evidence_gate_impact import build_payload


class Phase27SemanticGateImpactTests(unittest.TestCase):
    def test_semantic_evidence_alone_does_not_pending_or_upgrade_high(self):
        payload = build_payload(sqlite3.connect(":memory:"), tickers="300394.SZ", mode="mock")
        self.assertEqual(payload["summary"]["new_pending_created"], 0)
        self.assertEqual(payload["summary"]["promotion_allowed_from_semantic_evidence_only"], 0)
        row = payload["ticker_results"][0]
        self.assertNotEqual(row["confidence_after"], "high")
        self.assertIn("supplier share still not disclosed", row["why_not_upgraded"])


if __name__ == "__main__":
    unittest.main()
