import json
import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_financial_statement_chunker import evidence_item_for_chunk, upsert_financial_statement_chunks


class Phase17ChunkEvidenceLinkageTests(unittest.TestCase):
    def test_financial_statement_chunk_links_to_evidence(self):
        conn = sqlite3.connect(":memory:")
        source = {
            "source_id": "cninfo_300308_fixture",
            "source_type": "annual_report",
            "source_url": "https://example.test/300308.pdf",
            "published_at": "2026-03-31",
            "title": "2025 annual report",
            "provider": "cninfo",
        }
        chunk = {
            "chunk_id": "chunk_income_300308",
            "ticker": "300308.SZ",
            "source_id": source["source_id"],
            "section_type": "income_statement",
            "section_title": "合并利润表",
            "table_text": "合并利润表\n营业收入 12000000000\n营业成本 8000000000",
            "confidence": 0.82,
            "source_url": source["source_url"],
            "published_at": source["published_at"],
        }
        payload = upsert_financial_statement_chunks(conn, "300308.SZ", source, [chunk])
        self.assertEqual(payload["chunks_linked"], 1)
        evidence_id = payload["evidence_linked"][0]["evidence_id"]
        row = conn.execute("SELECT source_type, source_quality, metadata_json FROM evidence_items WHERE evidence_id=?", (evidence_id,)).fetchone()
        self.assertEqual(row[0], "filing")
        self.assertEqual(row[1], "primary")
        metadata = json.loads(row[2])
        self.assertEqual(metadata["section_type"], "income_statement")
        self.assertTrue(metadata["usable_for_fundamentals"])

    def test_evidence_quality_degrades_for_low_confidence_highlights(self):
        item = evidence_item_for_chunk(
            {
                "chunk_id": "chunk_highlights",
                "ticker": "300308.SZ",
                "source_id": "src",
                "section_type": "financial_highlights",
                "confidence": 0.5,
                "table_text": "主要会计数据和财务指标",
            }
        )
        self.assertEqual(item["source_status"], "degraded")
        self.assertFalse(item["metadata"]["usable_for_fundamentals"])


if __name__ == "__main__":
    unittest.main()
