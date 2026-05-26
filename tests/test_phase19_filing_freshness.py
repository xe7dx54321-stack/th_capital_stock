import sqlite3
import sys
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_claim_graph import ensure_claim_graph_tables, upsert_evidence
from smr_filing_freshness import build_filing_freshness


class Phase19FilingFreshnessTests(unittest.TestCase):
    def _conn_with_filing(self, published_at):
        conn = sqlite3.connect(":memory:")
        ensure_claim_graph_tables(conn)
        upsert_evidence(
            conn,
            {
                "evidence_id": f"ev_{published_at}",
                "source_key": "cninfo_TEST",
                "source_type": "filing",
                "source_quality": "primary",
                "source_status": "active",
                "published_at": published_at,
                "ingested_at": published_at,
                "text_excerpt": "TEST 2026 quarterly report revenue and profit.",
                "url_or_doc_id": "https://example.com/report",
                "metadata": {"ticker": "TEST.SZ"},
            },
        )
        return conn

    def test_fresh_filing_does_not_block_pending(self):
        conn = self._conn_with_filing("2026-04-30")
        payload = build_filing_freshness(conn, "TEST.SZ", now=datetime(2026, 5, 26))

        self.assertEqual(payload["filing_freshness"]["status"], "fresh")
        self.assertTrue(payload["filing_freshness"]["usable_for_promotion"])
        self.assertEqual(payload["blocking_effect"], "none")

    def test_stale_filing_blocks_pending(self):
        conn = self._conn_with_filing("2025-01-01")
        payload = build_filing_freshness(conn, "TEST.SZ", now=datetime(2026, 5, 26))

        self.assertEqual(payload["filing_freshness"]["status"], "stale")
        self.assertFalse(payload["filing_freshness"]["usable_for_promotion"])
        self.assertEqual(payload["blocking_effect"], "block_pending_review")


if __name__ == "__main__":
    unittest.main()
