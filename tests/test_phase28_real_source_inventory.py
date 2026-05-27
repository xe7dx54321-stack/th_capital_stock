import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
REPORTING_DIR = ROOT / "08_scripts" / "reporting"
TEST_DIR = ROOT / "tests"
for path in (LIB_DIR, REPORTING_DIR, TEST_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase28_ir_source_inventory import build_payload
from test_phase28_real_ir_source_connector import make_real_ir_conn


class Phase28RealSourceInventoryTests(unittest.TestCase):
    def test_real_source_preferred_and_mock_fallback_explicit(self):
        conn = make_real_ir_conn()
        conn.execute(
            "INSERT INTO filing_documents VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("300308.SZ", "中际旭创：投资者关系活动记录表", "cn_exchange_announcement", "2026-05-01", "2026-05-02", "cninfo_announcement", "https://static.cninfo.com.cn/real.pdf", None, "{}"),
        )
        payload = build_payload(conn, tickers="300308.SZ,300394.SZ", allow_mock_fallback=True)
        self.assertEqual(payload["summary"]["tickers_checked"], 2)
        self.assertEqual(payload["ticker_results"][0]["real_sources_found"], 1)
        self.assertFalse(payload["ticker_results"][0]["mock_fallback_used"])
        self.assertTrue(payload["ticker_results"][1]["mock_fallback_used"])


if __name__ == "__main__":
    unittest.main()
