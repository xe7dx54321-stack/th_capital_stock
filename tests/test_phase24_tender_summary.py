import sqlite3
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
REPORTING_DIR = ROOT / "08_scripts" / "reporting"
for path in (LIB_DIR, REPORTING_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase24_cn_tender_procurement_summary import build_payload, render_markdown
from smr_source_connector_registry import get_routes_for_information_type


class Phase24TenderSummaryTests(unittest.TestCase):
    def test_summary_json_markdown_and_registry_status(self):
        ticker_payload = {
            "ticker": "688041.SH",
            "company_name": "海光信息",
            "queries_generated": 12,
            "raw_results_found": 1,
            "normalized_items": 1,
            "normalized_results": [{"evidence_strength": "strong_indication"}],
            "evidence_candidates": [{"ticker": "688041.SH", "source_subtype": "tender_award", "evidence_strength": "strong_indication", "source_url": "https://example.com"}],
        }
        with patch("build_phase24_cn_tender_procurement_summary.build_cn_tender_procurement_payload", return_value=ticker_payload):
            payload = build_payload(sqlite3.connect(":memory:"), tickers="688041.SH")
        self.assertEqual(payload["best_evidence_strength"], "strong_indication")
        self.assertIn("Phase 24", render_markdown({"summary": {"tickers_checked": 1}, "rows": [payload], "evidence_candidates": []}))
        route = get_routes_for_information_type("tender_award", "CN")
        cn_tender = next(source for source in route["preferred_sources"] if source["connector_id"] == "cn_tender_procurement")
        self.assertEqual(cn_tender["status"], "partial")


if __name__ == "__main__":
    unittest.main()
