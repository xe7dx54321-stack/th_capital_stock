import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_direct_demand_evidence import extract_direct_demand_evidence, summarize_demand_evidence


class Phase21DirectDemandExtractorTests(unittest.TestCase):
    def test_extracts_and_deduplicates_independent_sources(self):
        conn = sqlite3.connect(":memory:")
        conn.execute(
            """
            CREATE TABLE document_chunks (
                chunk_id TEXT,
                evidence_id TEXT,
                source_key TEXT,
                document_type TEXT,
                chunk_section_type TEXT,
                text TEXT,
                metadata_json TEXT,
                ticker TEXT,
                created_at TEXT,
                chunk_index INTEGER
            )
            """
        )
        for idx in range(2):
            conn.execute(
                """
                INSERT INTO document_chunks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"chunk_{idx}",
                    f"ev_{idx}",
                    "cninfo",
                    "filing",
                    "management_discussion",
                    "AI服务器和数据中心需求增长，公司客户认可度提升。",
                    '{"source_id":"same_filing","published_at":"2026-04-30"}',
                    "TEST.SZ",
                    "2026-05-01 00:00:00",
                    idx,
                ),
            )

        items = extract_direct_demand_evidence(conn, "TEST.SZ", limit=10, persist=True)
        summary = summarize_demand_evidence("TEST.SZ", items)

        self.assertGreaterEqual(len(items), 1)
        self.assertEqual(summary["independent_source_count"], 1)
        self.assertEqual(summary["dominant_direction"], "positive")
        self.assertTrue(summary["usable_for_bear_case_mitigation"])


if __name__ == "__main__":
    unittest.main()
