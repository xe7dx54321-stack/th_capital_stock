import json
import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_claim_graph import ensure_claim_graph_tables
from smr_data_health import ensure_data_health_tables
from smr_filings_ingestion import seed_filing_document, update_filings_health_rows
from smr_news_ingestion import seed_news_item, update_news_health_rows


def memory_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    ensure_data_health_tables(conn)
    ensure_claim_graph_tables(conn)
    return conn


class NewsFilingsFreshnessTests(unittest.TestCase):
    def test_news_health_keeps_source_market_rows(self):
        conn = memory_conn()
        seed_news_item(conn, "NVDA AI demand update", ticker="NVDA", market="US")
        seed_news_item(conn, "09988.HK cloud demand update", ticker="09988.HK", market="H")

        snapshot = update_news_health_rows(conn)
        rows = conn.execute(
            "SELECT source_key, market, freshness_status FROM data_source_health WHERE data_type='news'"
        ).fetchall()

        self.assertEqual(snapshot["overall_status"], "fresh")
        self.assertIn(("manual_news", "US", "fresh"), rows)
        self.assertIn(("manual_news", "H", "fresh"), rows)

    def test_filings_health_keeps_ticker_level_rows(self):
        conn = memory_conn()
        seed_filing_document(conn, "NVDA", "NVDA 10-Q", "NVDA revenue and risk factors.", source_key="sec_filing_document", market="US")
        seed_filing_document(conn, "09988.HK", "09988.HK HKEX announcement", "09988.HK operating update.", source_key="hkex_announcement", market="H")

        snapshot = update_filings_health_rows(conn)
        rows = conn.execute(
            "SELECT source_key, market, metadata_json FROM data_source_health WHERE data_type='filings'"
        ).fetchall()
        metadata = [json.loads(row[2] or "{}") for row in rows]

        self.assertEqual(snapshot["overall_status"], "fresh")
        self.assertTrue(any(row[0] == "sec_filing_document:NVDA" and row[1] == "US" for row in rows))
        self.assertTrue(any(row[0] == "hkex_announcement:09988.HK" and row[1] == "H" for row in rows))
        self.assertTrue(any(item.get("ticker") == "NVDA" for item in metadata))
        self.assertTrue(any(item.get("ticker") == "09988.HK" for item in metadata))


if __name__ == "__main__":
    unittest.main()
