import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
JOBS_DIR = ROOT / "08_scripts" / "jobs"
TEST_DIR = ROOT / "tests"
for path in (LIB_DIR, JOBS_DIR, TEST_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_semantic_ir_evidence import build_payload
from test_phase28_real_ir_source_connector import make_real_ir_conn


class Phase28SemanticExtractionRealSourcesTests(unittest.TestCase):
    def test_real_source_semantic_extraction_keeps_url_and_quote(self):
        conn = make_real_ir_conn()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ir.md"
            text = "## Extracted Text\n\n问：高速光器件需求和产能情况如何？\n答：公司推进高速光器件产能建设，以满足客户需求增长。"
            path.write_text(text, encoding="utf-8")
            conn.execute(
                "INSERT INTO filing_documents VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                ("300394.SZ", "天孚通信：投资者关系活动记录表", "cn_exchange_announcement", "2026-05-01", "2026-05-02", "cninfo_announcement", "https://static.cninfo.com.cn/a.pdf", str(path), "{}"),
            )
            payload = build_payload(tickers="300394.SZ", conn=conn, use_real_sources=True, mode="mock")
        self.assertEqual(payload["summary"]["real_sources_used"], 1)
        self.assertGreater(payload["summary"]["semantic_extractions"], 0)
        item = payload["ticker_results"][0]["semantic_extractions"][0]
        self.assertTrue(item["quoted_span"])
        self.assertEqual(payload["summary"]["mock_sources_used"], 0)


if __name__ == "__main__":
    unittest.main()
