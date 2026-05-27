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
from persist_semantic_evidence_candidates import build_payload
from smr_real_ir_source_connector import stable_real_ir_source_id
from smr_semantic_evidence_persistence import gate_result_to_candidate, write_semantic_evidence_candidates
from test_phase28_real_ir_source_connector import make_real_ir_conn


class Phase29SemanticEvidencePersistenceTests(unittest.TestCase):
    def test_use_text_cache_dry_run_creates_candidates_and_execute_dedupes(self):
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
                smr_text_cache.write_text_cache({"source_id": source_id, "ticker": "300394.SZ", "source_url": "https://static.cninfo.com.cn/a.pdf"}, "答：公司推进高速光器件产能建设，以满足客户需求增长。" * 10)
                dry = build_payload(conn, tickers="300394.SZ", mode="dry_run", use_text_cache=True)
                self.assertGreater(dry["summary"]["evidence_candidates_created"], 0)
                self.assertFalse(dry["summary"]["dry_run_wrote_db"])
                candidates = dry["rows"][0]["evidence_candidates"]
                write_semantic_evidence_candidates(conn, candidates)
                write_semantic_evidence_candidates(conn, candidates)
                self.assertEqual(conn.execute("SELECT COUNT(*) FROM semantic_evidence_candidates").fetchone()[0], len(candidates))
            finally:
                smr_text_cache.TEXT_CACHE_DIR = original

    def test_quote_must_be_in_chunk_and_url_required(self):
        self.assertIsNone(gate_result_to_candidate({"evidence_status": "partial", "source_id": "s", "chunk_id": "c", "variable_type": "capacity_signal", "extraction": {"quoted_span": "missing"}}, chunk={"text": "other", "metadata": {"source_url": "https://x"}}))
        self.assertIsNone(gate_result_to_candidate({"evidence_status": "partial", "source_id": "s", "chunk_id": "c", "variable_type": "capacity_signal", "extraction": {"quoted_span": "x"}}, chunk={"text": "x", "metadata": {}}))


if __name__ == "__main__":
    unittest.main()
