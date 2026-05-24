import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
JOBS_DIR = ROOT / "08_scripts" / "jobs"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
if str(JOBS_DIR) not in sys.path:
    sys.path.insert(0, str(JOBS_DIR))

from repair_valuation_snapshot import repair_valuation_for_ticker
from smr_valuation import build_valuation_snapshot, valuation_sub_blockers


class Phase10PriceValuationRepairTests(unittest.TestCase):
    def test_fresh_snapshot_price_stale_does_not_emit_valuation_stale(self):
        blockers = valuation_sub_blockers(
            {
                "allowed_usage": "blocked_due_to_stale_price",
                "valuation_status": "fresh_snapshot_price_stale",
                "missing_data": ["fresh_price", "forward_eps"],
                "valuation_confidence": 0.5,
            }
        )
        codes = {item["code"] for item in blockers}

        self.assertIn("PRICE_STALE", codes)
        self.assertNotIn("VALUATION_STALE", codes)

    def test_repair_execute_recomputes_snapshot_without_promotion_fabrication(self):
        conn = sqlite3.connect(":memory:")
        conn.execute("CREATE TABLE daily_bar (ts_code TEXT, market TEXT, trade_date TEXT, close REAL)")
        conn.execute("INSERT INTO daily_bar VALUES ('09988.HK', 'H', '2026-05-21', 126.0)")

        payload = repair_valuation_for_ticker(conn, "09988.HK", dry_run=False)

        self.assertEqual(payload["mode"], "execute")
        self.assertIn("after", payload)
        self.assertNotEqual(payload["after"]["allowed_usage"], "promotion_eligible")
        self.assertIn("recompute_valuation_snapshot", payload["repair_actions"])

    def test_build_snapshot_records_price_date_and_inputs(self):
        conn = sqlite3.connect(":memory:")
        conn.execute("CREATE TABLE daily_bar (ts_code TEXT, market TEXT, trade_date TEXT, close REAL)")
        conn.execute("INSERT INTO daily_bar VALUES ('09988.HK', 'H', '2026-05-21', 126.0)")

        snapshot = build_valuation_snapshot(conn, "09988.HK", data_health_snapshot={"items": []})

        self.assertEqual(snapshot["price_trade_date"], "2026-05-21")
        self.assertIn("forward_eps", snapshot)
        self.assertIn("historical_valuation", snapshot)


if __name__ == "__main__":
    unittest.main()
