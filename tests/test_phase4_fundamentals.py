import sqlite3
import sys
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_fundamentals import build_fundamentals_snapshot, latest_fundamentals_snapshot
from smr_fundamentals import build_us_fundamentals
from smr_valuation import build_valuation_snapshot


def make_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE daily_bar (
            ts_code TEXT,
            market TEXT,
            trade_date TEXT,
            close REAL
        );
        CREATE TABLE factor_daily (
            ts_code TEXT,
            trade_date TEXT,
            factor_name TEXT,
            factor_value REAL
        );
        """
    )
    return conn


class Phase4FundamentalsTests(unittest.TestCase):
    def test_factor_fundamentals_snapshot_is_ticker_level_and_explainable(self):
        conn = make_conn()
        today = datetime.now().strftime("%Y-%m-%d")
        factors = {
            "revenue": 1000.0,
            "net_profit": 120.0,
            "basic_eps_reported": 1.2,
            "gross_margin": 0.42,
            "ocf_per_share": 2.1,
        }
        for name, value in factors.items():
            conn.execute("INSERT INTO factor_daily VALUES ('000001.SZ', ?, ?, ?)", (today, name, value))

        snapshot = build_fundamentals_snapshot(conn, "000001.SZ", prefer_live=False)

        self.assertEqual(snapshot["ticker"], "000001.SZ")
        self.assertEqual(snapshot["freshness_status"], "fresh")
        self.assertEqual(snapshot["revenue"], 1000.0)
        self.assertIn("capex", snapshot["missing_fields"])
        self.assertTrue(snapshot["fundamentals_evidence_id"])
        self.assertEqual(latest_fundamentals_snapshot(conn, "000001.SZ")["snapshot_id"], snapshot["snapshot_id"])

    def test_valuation_reads_fundamentals_eps_proxy(self):
        conn = make_conn()
        today = datetime.now().strftime("%Y-%m-%d")
        conn.execute("INSERT INTO daily_bar VALUES ('000001.SZ', 'A', ?, 10.0)", (today,))
        conn.execute("INSERT INTO factor_daily VALUES ('000001.SZ', ?, 'pe_ttm', 8.0)", (today,))
        conn.execute("INSERT INTO factor_daily VALUES ('000001.SZ', ?, 'basic_eps_reported', 1.5)", (today,))
        conn.execute("INSERT INTO factor_daily VALUES ('000001.SZ', ?, 'revenue', 1000.0)", (today,))
        conn.execute("INSERT INTO factor_daily VALUES ('000001.SZ', ?, 'net_profit', 150.0)", (today,))
        conn.execute("INSERT INTO factor_daily VALUES ('000001.SZ', ?, 'gross_margin', 0.35)", (today,))
        build_fundamentals_snapshot(conn, "000001.SZ", prefer_live=False)

        valuation = build_valuation_snapshot(conn, "000001.SZ")

        self.assertEqual(valuation["ticker"], "000001.SZ")
        self.assertEqual(valuation["fundamentals_snapshot"]["freshness_status"], "fresh")
        self.assertEqual(valuation["broker_forward_eps_proxy"], 1.5)
        self.assertIn(valuation["allowed_usage"], {"supporting_evidence", "promotion_eligible"})

    def test_us_fundamentals_do_not_compute_margins_across_periods(self):
        companyfacts = {
            "facts": {
                "us-gaap": {
                    "RevenueFromContractWithCustomerExcludingAssessedTax": {
                        "units": {
                            "USD": [
                                {"val": 100.0, "end": "2026-03-31", "filed": "2026-04-20", "fy": 2026, "fp": "Q1"}
                            ]
                        }
                    },
                    "GrossProfit": {
                        "units": {
                            "USD": [
                                {"val": 80.0, "end": "2025-12-31", "filed": "2026-02-20", "fy": 2025, "fp": "FY"}
                            ]
                        }
                    },
                    "NetIncomeLoss": {
                        "units": {
                            "USD": [
                                {"val": 20.0, "end": "2026-03-31", "filed": "2026-04-20", "fy": 2026, "fp": "Q1"}
                            ]
                        }
                    },
                }
            }
        }

        original = __import__("smr_fundamentals").fetch_sec_companyfacts
        try:
            __import__("smr_fundamentals").fetch_sec_companyfacts = lambda _symbol, timeout=30: (companyfacts, {"cik": 1})
            values, metadata = build_us_fundamentals("TEST")
        finally:
            __import__("smr_fundamentals").fetch_sec_companyfacts = original

        self.assertIsNone(values.get("gross_margin"))
        self.assertIn("gross_margin", " ".join(metadata["period_mismatches"]))


if __name__ == "__main__":
    unittest.main()
