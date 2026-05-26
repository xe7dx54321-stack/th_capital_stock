import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_cninfo_source_identity import resolve_cninfo_source_identity
from smr_financial_statement_source_discovery import discover_financial_statement_sources


class Phase18CninfoSourceIdentityTests(unittest.TestCase):
    def test_resolves_688041_cninfo_identity(self):
        identity = resolve_cninfo_source_identity("688041.SH", manifest={"source_identities": {}})
        self.assertEqual(identity["status"], "resolved")
        self.assertEqual(identity["org_id"], "9900048365")
        self.assertEqual(identity["exchange"], "SSE")

    def test_source_discovery_uses_manifest_source(self):
        manifest = {
            "version": 1,
            "source_identities": {"688041.SH": {"org_id": "9900048365", "plate": "sh", "column": "sse", "exchange": "SSE"}},
            "sources": {
                "688041.SH": [
                    {
                        "source_id": "cninfo_688041_fixture",
                        "source_type": "annual_report",
                        "source_url": "https://example.test/688041.pdf",
                        "published_at": "2026-04-08",
                        "title": "2025年年度报告",
                        "document_format": "pdf",
                        "expected_sections": ["income_statement", "balance_sheet", "cash_flow_statement"],
                        "status": "active",
                    }
                ]
            },
        }
        payload = discover_financial_statement_sources(sqlite3.connect(":memory:"), "688041.SH", live=False, manifest=manifest)
        self.assertEqual(payload["best_source"]["source_id"], "cninfo_688041_fixture")
        self.assertEqual(payload["source_identity"]["status"], "resolved")

    def test_unresolved_identity_has_specific_reason(self):
        identity = resolve_cninfo_source_identity("689999.SH", manifest={"source_identities": {}, "sources": {}})
        self.assertEqual(identity["status"], "unresolved")
        self.assertEqual(identity["missing_reason"], "cninfo_org_id_missing")


if __name__ == "__main__":
    unittest.main()
