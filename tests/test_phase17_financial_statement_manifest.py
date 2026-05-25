import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_financial_statement_source_discovery import (
    load_financial_statement_manifest,
    validate_financial_statement_manifest,
)


class Phase17FinancialStatementManifestTests(unittest.TestCase):
    def test_manifest_load_and_validate(self):
        manifest = load_financial_statement_manifest(ROOT / "00_control" / "financial_statement_sources.json")
        result = validate_financial_statement_manifest(manifest)
        self.assertTrue(result["valid"], result["errors"])
        self.assertIn("00700.HK", manifest["sources"])
        self.assertIn("300308.SZ", manifest["sources"])

    def test_missing_source_url_is_reported(self):
        manifest = {
            "version": 1,
            "sources": {
                "TEST.HK": [
                    {
                        "source_id": "src",
                        "source_type": "annual_report",
                        "published_at": "2026-01-01",
                        "expected_sections": ["balance_sheet"],
                        "status": "active",
                    }
                ]
            },
        }
        result = validate_financial_statement_manifest(manifest)
        self.assertFalse(result["valid"])
        self.assertIn("TEST.HK:0:source_url_missing", result["errors"])


if __name__ == "__main__":
    unittest.main()
