import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for rel in [("08_scripts", "lib"), ("08_scripts", "reporting")]:
    path = ROOT.joinpath(*rel)
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase19_thesis_evidence_gate import build_ticker_payload


class Phase19ThesisEvidenceGateTests(unittest.TestCase):
    def test_metadata_confidence_does_not_allow_pending_without_evidence(self):
        conn = sqlite3.connect(":memory:")
        payload = build_ticker_payload(conn, "002230.SZ", watchlist_id="ai_core")

        self.assertFalse(payload["before"]["allow_pending"])
        self.assertFalse(payload["after_metadata_simulation"]["allow_pending"])
        self.assertIn(payload["thesis_evidence_gate"]["status"], {"unknown_thesis", "evidence_insufficient"})
        self.assertIn("claim_graph_support", payload["thesis_evidence_gate"]["missing_evidence"])


if __name__ == "__main__":
    unittest.main()
