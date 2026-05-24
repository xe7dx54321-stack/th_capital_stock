import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_valuation import build_historical_valuation, valuation_sub_blockers


class Phase11HistoricalValuationDataTests(unittest.TestCase):
    def test_pb_historical_percentile_available_with_enough_samples(self):
        conn = sqlite3.connect(":memory:")
        conn.execute("CREATE TABLE factor_daily (ts_code TEXT, trade_date TEXT, factor_name TEXT, factor_value REAL)")
        for index in range(70):
            conn.execute(
                "INSERT INTO factor_daily VALUES ('09988.HK', ?, 'pb', ?)",
                (f"2026-03-{(index % 28) + 1:02d}", 1.0 + index / 100),
            )

        historical = build_historical_valuation(conn, "09988.HK", {"pb": 1.35})

        self.assertEqual(historical["metrics"]["pb"]["status"], "available")
        self.assertGreaterEqual(historical["metrics"]["pb"]["sample_count"], 60)

    def test_available_historical_snapshot_does_not_emit_missing_metric_blocker(self):
        blockers = valuation_sub_blockers(
            {
                "historical_valuation": {"status": "available", "missing_reasons": ["ps_ttm_missing"]},
                "historical_percentile": 0.42,
                "historical_percentile_status": "available",
                "valuation_confidence": 0.5,
            }
        )

        self.assertNotIn("HISTORICAL_FUNDAMENTALS_MISSING", {item["code"] for item in blockers})


if __name__ == "__main__":
    unittest.main()
