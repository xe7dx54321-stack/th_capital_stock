import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
JOBS_DIR = ROOT / "08_scripts" / "jobs"
for path in (LIB_DIR, JOBS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from fetch_real_ir_sources import build_payload
from smr_real_ir_source_connector import normalize_real_ir_source, stable_real_ir_source_id


def make_real_ir_conn():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE filing_documents (
            ticker TEXT, title TEXT, filing_type TEXT, published_at TEXT, ingested_at TEXT,
            source_key TEXT, source_url TEXT, parsed_text_path TEXT, metadata_json TEXT
        )
        """
    )
    return conn


class Phase28RealIRSourceConnectorTests(unittest.TestCase):
    def test_dry_run_normalizes_real_source_without_write(self):
        conn = make_real_ir_conn()
        conn.execute(
            "INSERT INTO filing_documents VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("300394.SZ", "天孚通信：投资者关系活动记录表", "cn_exchange_announcement", "2026-05-01", "2026-05-02", "cninfo_announcement", "https://static.cninfo.com.cn/a.pdf", None, "{}"),
        )
        payload = build_payload(conn, ticker="300394.SZ", mode="dry_run")
        self.assertEqual(payload["sources_found"], 1)
        self.assertEqual(payload["sources_written"], 0)
        self.assertEqual(payload["normalized_sources"][0]["source_type"], "investor_relations_record")
        self.assertFalse(payload["normalized_sources"][0]["raw_content_saved"])
        self.assertFalse(conn.execute("SELECT 1 FROM sqlite_master WHERE name='real_ir_sources'").fetchone())

    def test_source_url_missing_downgrades_and_source_id_stable(self):
        a = stable_real_ir_source_id("300394.SZ", "https://x", "title")
        b = stable_real_ir_source_id("300394.SZ", "https://x", "other")
        self.assertEqual(a, b)
        source = normalize_real_ir_source(ticker="300394.SZ", company_name="天孚通信", source_type="unknown", title="x", published_at=None, source_url=None)
        self.assertEqual(source["allowed_usage"], "context_only")
        self.assertEqual(source["freshness_status"], "freshness_unknown")


if __name__ == "__main__":
    unittest.main()
