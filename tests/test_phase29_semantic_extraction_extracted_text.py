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

import smr_text_cache
from build_semantic_ir_evidence import build_payload
from smr_real_ir_source_connector import stable_real_ir_source_id
from test_phase28_real_ir_source_connector import make_real_ir_conn


class Phase29SemanticExtractionExtractedTextTests(unittest.TestCase):
    def test_semantic_extraction_uses_text_cache_and_validates_quote(self):
        conn = make_real_ir_conn()
        conn.execute(
            "INSERT INTO filing_documents VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("300394.SZ", "天孚通信：投资者关系活动记录表", "cn_exchange_announcement", "2026-05-01", "2026-05-02", "cninfo_announcement", "https://static.cninfo.com.cn/a.pdf", None, "{}"),
        )
        with tempfile.TemporaryDirectory() as tmp:
            original = smr_text_cache.TEXT_CACHE_DIR
            smr_text_cache.TEXT_CACHE_DIR = Path(tmp) / "text_cache"
            try:
                source_id = stable_real_ir_source_id("300394.SZ", "https://static.cninfo.com.cn/a.pdf", "天孚通信：投资者关系活动记录表")
                smr_text_cache.write_text_cache({"source_id": source_id, "ticker": "300394.SZ", "source_url": "https://static.cninfo.com.cn/a.pdf"}, "问：高速光器件需求和产能情况如何？\n答：公司推进高速光器件产能建设，以满足客户需求增长。" * 8)
                payload = build_payload(tickers="300394.SZ", conn=conn, use_real_sources=True, use_text_cache=True, mode="mock")
            finally:
                smr_text_cache.TEXT_CACHE_DIR = original
        self.assertGreater(payload["summary"]["semantic_extractions"], 0)
        self.assertEqual(payload["summary"]["quoted_span_validated"], payload["summary"]["semantic_extractions"])
        self.assertEqual(payload["summary"]["source_url_preserved"], payload["summary"]["semantic_extractions"])


if __name__ == "__main__":
    unittest.main()
