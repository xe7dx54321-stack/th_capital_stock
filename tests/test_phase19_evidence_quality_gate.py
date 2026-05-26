import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_claim_graph import ensure_claim_graph_tables, upsert_evidence
from smr_evidence_quality import build_evidence_quality_gate, phase19_quality_dimensions


class Phase19EvidenceQualityGateTests(unittest.TestCase):
    def test_primary_field_linked_evidence_is_high_quality(self):
        conn = sqlite3.connect(":memory:")
        ensure_claim_graph_tables(conn)
        upsert_evidence(
            conn,
            {
                "evidence_id": "ev_high",
                "source_key": "cninfo_TEST",
                "source_type": "filing",
                "source_quality": "primary",
                "source_status": "active",
                "published_at": "2026-04-30",
                "ingested_at": "2026-04-30",
                "text_excerpt": "TEST.SZ revenue increased 30 percent and gross profit improved in the income statement.",
                "url_or_doc_id": "https://example.com/report",
                "metadata": {
                    "ticker": "TEST.SZ",
                    "chunk_section_type": "financial_statement",
                    "investment_relevance_score": 0.9,
                    "usable_for_core_claim": True,
                },
            },
        )

        payload = build_evidence_quality_gate(conn, "TEST.SZ")

        self.assertGreaterEqual(payload["evidence_quality_gate"]["high_quality_evidence_count"], 1)
        self.assertTrue(payload["evidence_quality_gate"]["usable_for_promotion"])

    def test_missing_evidence_id_is_blocked(self):
        dimensions = phase19_quality_dimensions(
            {
                "evidence_id": None,
                "source_type": "filing",
                "source_quality": "primary",
                "source_status": "active",
                "published_at": "2026-04-30",
                "ingested_at": "2026-04-30",
                "text_excerpt": "TEST revenue growth.",
                "metadata_json": {"ticker": "TEST"},
            },
            ticker="TEST",
        )

        self.assertEqual(dimensions["quality_level"], "blocked")
        self.assertFalse(dimensions["usable_for_promotion"])


if __name__ == "__main__":
    unittest.main()
