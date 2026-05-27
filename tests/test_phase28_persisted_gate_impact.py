import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
VERIFICATION_DIR = ROOT / "08_scripts" / "verification"
TEST_DIR = ROOT / "tests"
for path in (LIB_DIR, VERIFICATION_DIR, TEST_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from test_phase28_real_ir_source_connector import make_real_ir_conn
from validate_phase28_persisted_semantic_gate_impact import build_payload


class Phase28PersistedGateImpactTests(unittest.TestCase):
    def test_semantic_evidence_alone_does_not_pending(self):
        conn = make_real_ir_conn()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ir.md"
            path.write_text("## Extracted Text\n\n答：公司推进高速光器件产能建设，以满足客户需求增长。", encoding="utf-8")
            conn.execute(
                "INSERT INTO filing_documents VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                ("300394.SZ", "天孚通信：投资者关系活动记录表", "cn_exchange_announcement", "2026-05-01", "2026-05-02", "cninfo_announcement", "https://static.cninfo.com.cn/a.pdf", str(path), "{}"),
            )
            payload = build_payload(conn, tickers="300394.SZ")
        self.assertEqual(payload["summary"]["new_pending_created"], 0)
        self.assertEqual(payload["summary"]["promotion_allowed_from_semantic_evidence_only"], 0)
        self.assertIn("supplier share still not disclosed", payload["ticker_results"][0]["why_not_upgraded"])


if __name__ == "__main__":
    unittest.main()
