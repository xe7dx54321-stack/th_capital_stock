import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase36_300394_evidence_chain_diagnostics import build_payload, render_markdown


class Phase36300394EvidenceChainDiagnosticsTests(unittest.TestCase):
    def test_diagnostics_cover_zero_chain_stages(self):
        payload = build_payload(sqlite3.connect(":memory:"))
        body = payload["evidence_chain_zero_diagnostics"]
        checks = {row["check"]: row for row in body["checks"]}
        self.assertEqual(body["evidence_chain_count"], 0)
        self.assertEqual(body["diagnostic_status"], "needs_repair")
        self.assertGreaterEqual(len(checks), 10)
        for check in (
            "source_inventory",
            "text_cache",
            "semantic_extraction",
            "semantic_candidates_created",
            "persisted_evidence",
            "ticker_mapping",
            "local_db_state",
        ):
            self.assertIn(check, checks)
        self.assertTrue(body["likely_root_causes"])
        self.assertFalse(payload["safety"]["fake_evidence_written"])
        self.assertIn("Phase 36 300394 Evidence Chain Diagnostics", render_markdown(payload))


if __name__ == "__main__":
    unittest.main()
