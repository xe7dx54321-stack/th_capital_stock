import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_financial_statement_source_discovery import (
    choose_best_source,
    discover_financial_statement_sources,
    rank_sources,
)


class Phase17FinancialStatementSourceDiscoveryTests(unittest.TestCase):
    def test_manifest_source_discovery_returns_best_source(self):
        manifest = {
            "version": 1,
            "sources": {
                "00700.HK": [
                    {
                        "source_id": "hkex_00700_2025_annual",
                        "source_type": "annual_report",
                        "source_url": "https://example.test/00700.pdf",
                        "published_at": "2026-04-09",
                        "title": "Annual Report 2025",
                        "document_format": "pdf",
                        "expected_sections": ["income_statement", "balance_sheet", "cash_flow_statement"],
                        "status": "active",
                    }
                ]
            },
        }
        payload = discover_financial_statement_sources(sqlite3.connect(":memory:"), "00700.HK", live=False, manifest=manifest)
        self.assertEqual(payload["market"], "HK")
        self.assertEqual(payload["best_source"]["source_id"], "hkex_00700_2025_annual")
        self.assertTrue(payload["best_source"]["source_url"])

    def test_source_ranking_prefers_annual_report_then_freshness(self):
        sources = [
            {"source_id": "quarter", "source_type": "quarterly_report", "published_at": "2026-05-01", "confidence": 0.95, "has_financial_tables": True},
            {"source_id": "annual", "source_type": "annual_report", "published_at": "2026-03-31", "confidence": 0.8, "has_financial_tables": True},
            {"source_id": "old_annual", "source_type": "annual_report", "published_at": "2025-03-31", "confidence": 0.99, "has_financial_tables": True},
        ]
        self.assertEqual(rank_sources(sources)[0]["source_id"], "annual")
        self.assertEqual(choose_best_source(sources)["source_id"], "annual")

    def test_missing_source_has_explicit_reason(self):
        payload = discover_financial_statement_sources(sqlite3.connect(":memory:"), "688041.SH", live=False, manifest={"version": 1, "sources": {}})
        self.assertEqual(payload["sources_found"], [])
        self.assertEqual(payload["missing_reason"], "financial_statement_source_not_found")


if __name__ == "__main__":
    unittest.main()
