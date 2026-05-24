import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_fundamentals import historical_fundamental_support


class Phase11HistoricalFundamentalsSupportTests(unittest.TestCase):
    def test_revenue_and_equity_attempt_are_period_level(self):
        conn = sqlite3.connect(":memory:")
        conn.execute("CREATE TABLE factor_daily (ts_code TEXT, trade_date TEXT, factor_name TEXT, factor_value REAL)")
        conn.execute("INSERT INTO factor_daily VALUES ('09988.HK', 'FY2025', 'revenue', 1000)")
        conn.execute("INSERT INTO factor_daily VALUES ('09988.HK', 'FY2025', 'bps_reported', 55)")

        support = historical_fundamental_support(conn, "09988.HK")

        self.assertEqual(support[0]["period"], "FY2025")
        self.assertEqual(support[0]["revenue"]["value"], 1000.0)
        self.assertEqual(support[0]["shareholders_equity"]["missing_reason"], "derived_field_missing_inputs")
        self.assertIn("book_value_per_share", support[0]["shareholders_equity"])


if __name__ == "__main__":
    unittest.main()
