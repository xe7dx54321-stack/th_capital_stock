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
from smr_valuation import valuation_sub_blockers


class Phase9ValuationRepairTests(unittest.TestCase):
    def test_valuation_blocker_split_is_specific(self):
        blockers = valuation_sub_blockers(
            {
                "allowed_usage": "blocked_due_to_stale_price",
                "valuation_status": "stale_price",
                "missing_data": ["fresh_price", "forward_eps", "historical_percentile", "peer_set"],
                "valuation_confidence": 0.2,
            },
            {"freshness_status": "fresh"},
        )
        codes = {item["code"] for item in blockers}

        self.assertIn("PRICE_STALE", codes)
        self.assertIn("FORWARD_EPS_MISSING", codes)
        self.assertIn("HISTORICAL_PERCENTILE_MISSING", codes)
        self.assertIn("PEER_SET_MISSING", codes)

    def test_repair_outputs_diagnostics_without_promotion_fabrication(self):
        conn = sqlite3.connect(":memory:")
        conn.execute("CREATE TABLE daily_bar (ts_code TEXT, market TEXT, trade_date TEXT, close REAL)")
        conn.execute("INSERT INTO daily_bar VALUES ('09988.HK', 'H', '2026-05-22', 80.0)")
        payload = repair_valuation_for_ticker(conn, "09988.HK", dry_run=True)

        self.assertEqual(payload["mode"], "dry_run")
        self.assertIn("diagnostics", payload)
        self.assertNotEqual(payload["after"]["allowed_usage"], "promotion_eligible")
        self.assertIn("FORWARD_EPS_MISSING", payload["after"]["remaining_blockers"])


if __name__ == "__main__":
    unittest.main()
