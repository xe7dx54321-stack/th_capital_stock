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

from persist_semantic_evidence_candidates import build_payload
from smr_semantic_evidence_persistence import ensure_semantic_evidence_candidate_table, gate_result_to_candidate, write_semantic_evidence_candidates
from test_phase28_real_ir_source_connector import make_real_ir_conn


class Phase28SemanticEvidencePersistenceTests(unittest.TestCase):
    def test_dry_run_does_not_write_and_execute_dedupes(self):
        conn = make_real_ir_conn()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ir.md"
            path.write_text("## Extracted Text\n\n答：公司推进高速光器件产能建设，以满足客户需求增长。", encoding="utf-8")
            conn.execute(
                "INSERT INTO filing_documents VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                ("300394.SZ", "天孚通信：投资者关系活动记录表", "cn_exchange_announcement", "2026-05-01", "2026-05-02", "cninfo_announcement", "https://static.cninfo.com.cn/a.pdf", str(path), "{}"),
            )
            dry = build_payload(conn, tickers="300394.SZ", mode="dry_run")
            self.assertGreaterEqual(dry["summary"]["evidence_candidates_created"], 1)
            self.assertFalse(conn.execute("SELECT 1 FROM sqlite_master WHERE name='semantic_evidence_candidates'").fetchone())
            candidates = dry["rows"][0]["evidence_candidates"]
            write_semantic_evidence_candidates(conn, candidates)
            write_semantic_evidence_candidates(conn, candidates)
            count = conn.execute("SELECT COUNT(*) FROM semantic_evidence_candidates").fetchone()[0]
            self.assertEqual(count, len(candidates))

    def test_missing_quote_or_url_not_written(self):
        bad = gate_result_to_candidate(
            {"evidence_status": "partial", "source_id": "s", "chunk_id": "c", "variable_type": "capacity_signal", "extraction": {"quoted_span": ""}},
            chunk={"metadata": {"source_url": "https://x"}},
        )
        self.assertIsNone(bad)


if __name__ == "__main__":
    unittest.main()
