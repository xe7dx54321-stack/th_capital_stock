import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_valuation import build_historical_valuation, valuation_sub_blockers


class Phase10HistoricalValuationTests(unittest.TestCase):
    def test_sample_insufficient_does_not_emit_strong_percentile(self):
        conn = sqlite3.connect(":memory:")
        conn.execute("CREATE TABLE factor_daily (ts_code TEXT, trade_date TEXT, factor_name TEXT, factor_value REAL)")
        for i in range(5):
            conn.execute("INSERT INTO factor_daily VALUES ('09988.HK', ?, 'ps_ttm', ?)", (f"2026-05-{i+1:02d}", 2.0 + i))

        historical = build_historical_valuation(conn, "09988.HK", {"ps_ttm": 3.0})

        self.assertEqual(historical["metrics"]["ps_ttm"]["status"], "missing")
        self.assertEqual(historical["metrics"]["ps_ttm"]["reason"], "sample_insufficient")

    def test_partial_historical_blocks_strong_conclusion(self):
        blockers = valuation_sub_blockers(
            {
                "historical_valuation": {"status": "partial", "missing_reasons": []},
                "historical_percentile_status": "partial",
                "valuation_confidence": 0.5,
            }
        )
        self.assertIn("HISTORICAL_PERCENTILE_PARTIAL", {item["code"] for item in blockers})


if __name__ == "__main__":
    unittest.main()
