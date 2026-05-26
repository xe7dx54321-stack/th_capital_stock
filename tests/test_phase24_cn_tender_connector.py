import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_cn_tender_procurement import build_cn_tender_procurement_payload
from smr_tender_evidence_linkage import ensure_tender_evidence_candidate_table


class Phase24TenderConnectorTests(unittest.TestCase):
    def test_dry_run_does_not_write_evidence_graph(self):
        conn = sqlite3.connect(":memory:")
        conn.execute(
            """
            CREATE TABLE news_items (
                news_id TEXT, source_key TEXT, source_name TEXT, title TEXT, body TEXT,
                url TEXT, published_at TEXT, ingested_at TEXT, metadata_json TEXT, tickers_json TEXT
            )
            """
        )
        conn.execute(
            "INSERT INTO news_items VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "n1",
                "local",
                "local news",
                "海光信息 中标结果公告",
                "海光信息 中标 算力服务器项目",
                "https://example.com/award",
                "2026-05-01",
                "2026-05-02",
                "{}",
                '["688041.SH"]',
            ),
        )
        payload = build_cn_tender_procurement_payload(conn, "688041.SH", execute=False)
        self.assertEqual(payload["mode"], "dry_run")
        self.assertGreaterEqual(len(payload["evidence_candidates"]), 1)
        ensure_tender_evidence_candidate_table(conn)
        self.assertEqual(conn.execute("SELECT count(*) FROM tender_procurement_evidence_candidates").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
