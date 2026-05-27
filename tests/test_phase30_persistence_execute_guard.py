import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
JOBS_DIR = ROOT / "08_scripts" / "jobs"
for path in (LIB_DIR, JOBS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from smr_semantic_evidence_persistence import (
    delete_semantic_evidence_candidates,
    guard_semantic_evidence_candidates,
    write_semantic_evidence_candidates,
)


def candidate(evidence_id="ev1", span="答：公司持续推进高速光模块产能建设，以满足客户需求增长。"):
    return {
        "evidence_id": evidence_id,
        "ticker": "300308.SZ",
        "theme": "ai_optical_interconnect",
        "source_id": "s1",
        "source_url": "https://static.cninfo.com.cn/a.pdf",
        "source_type": "investor_relations_record",
        "chunk_id": "chunk_0001",
        "quoted_span": span,
        "variable_type": "capacity_signal",
        "claim_text": span,
        "evidence_status": "partial",
        "allowed_usage": "scenario_analysis_only",
        "usable_for_expectation_gap": True,
        "usable_for_valuation_support": False,
        "usable_for_promotion": False,
        "limitations": ["management commentary"],
        "payload": {
            "source_metadata": {"real_source": True, "section_type": "qa_section", "published_at": "2026-05-01"},
            "gate": {"extraction": {"evidence_strength": "management_commentary", "is_company_specific": True}},
        },
    }


class Phase30PersistenceExecuteGuardTests(unittest.TestCase):
    def test_guard_filters_noisy_and_keeps_eligible(self):
        good = candidate("ev_good")
        noisy = candidate("ev_bad", "12%\n毛利\n114.")
        guarded = guard_semantic_evidence_candidates([good, noisy], reject_noisy=True)
        self.assertEqual(len(guarded["eligible_candidates"]), 1)
        self.assertEqual(guarded["summary"]["rejected_by_noise"], 1)

    def test_execute_writes_only_eligible_and_promotion_false(self):
        conn = sqlite3.connect(":memory:")
        good = candidate("ev_good")
        noisy = candidate("ev_bad", "12%\n毛利\n114.")
        written = write_semantic_evidence_candidates(conn, [good, noisy], enforce_quality_guard=True, reject_noisy=True)
        self.assertEqual(written, 1)
        row = conn.execute("SELECT usable_for_promotion FROM semantic_evidence_candidates").fetchone()
        self.assertEqual(row[0], 0)

    def test_execute_dedupes(self):
        conn = sqlite3.connect(":memory:")
        good = candidate("ev_good")
        write_semantic_evidence_candidates(conn, [good], enforce_quality_guard=True)
        write_semantic_evidence_candidates(conn, [good], enforce_quality_guard=True)
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM semantic_evidence_candidates").fetchone()[0], 1)

    def test_execute_can_remove_now_rejected_candidate(self):
        conn = sqlite3.connect(":memory:")
        good = candidate("ev_good")
        write_semantic_evidence_candidates(conn, [good], enforce_quality_guard=True)
        removed = delete_semantic_evidence_candidates(conn, [good])
        self.assertEqual(removed, 1)
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM semantic_evidence_candidates").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
