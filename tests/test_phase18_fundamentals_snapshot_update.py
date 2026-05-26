import sqlite3
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_fundamentals import ensure_fundamentals_tables, latest_fundamentals_snapshot
from smr_recovered_fundamentals import update_fundamentals_from_recovered_chunks


class Phase18FundamentalsSnapshotUpdateTests(unittest.TestCase):
    def test_recovered_00700_equity_updates_snapshot_with_lineage(self):
        conn = sqlite3.connect(":memory:")
        ensure_fundamentals_tables(conn)
        recovered = {
            "shareholders_equity": {
                "field": "shareholders_equity",
                "status": "extracted",
                "extracted_value": 1154.0,
                "source_evidence_id": "ev_equity",
                "source_evidence_ids": ["ev_equity"],
                "confidence": 0.82,
                "allowed_usage": "supporting_evidence",
            }
        }
        with patch("smr_recovered_fundamentals.recovered_fields_from_chunks", return_value=recovered):
            payload = update_fundamentals_from_recovered_chunks(conn, "00700.HK")
        update = payload["fundamentals_snapshot_update"]
        self.assertEqual(update["status"], "updated")
        self.assertEqual(update["fields_updated"][0]["source_evidence_id"], "ev_equity")
        snapshot = latest_fundamentals_snapshot(conn, "00700.HK")
        self.assertEqual(snapshot["shareholders_equity"], 1154.0)
        self.assertNotIn("shareholders_equity", snapshot["missing_fields"])

    def test_derived_gross_profit_requires_input_evidence_ids(self):
        conn = sqlite3.connect(":memory:")
        ensure_fundamentals_tables(conn)
        recovered = {
            "revenue": {"field": "revenue", "status": "extracted", "extracted_value": 100.0, "source_evidence_id": "ev_rev", "source_evidence_ids": ["ev_rev"], "confidence": 0.82, "allowed_usage": "supporting_evidence"},
            "gross_profit": {"field": "gross_profit", "status": "derived", "extracted_value": 30.0, "source_evidence_id": "ev_rev", "input_evidence_ids": [], "confidence": 0.74, "allowed_usage": "supporting_evidence"},
        }
        with patch("smr_recovered_fundamentals.recovered_fields_from_chunks", return_value=recovered):
            payload = update_fundamentals_from_recovered_chunks(conn, "300308.SZ")
        updated_fields = [item["field"] for item in payload["fundamentals_snapshot_update"]["fields_updated"]]
        skipped_fields = [item["field"] for item in payload["fundamentals_snapshot_update"]["fields_skipped"]]
        self.assertIn("revenue", updated_fields)
        self.assertIn("gross_profit", skipped_fields)


if __name__ == "__main__":
    unittest.main()
