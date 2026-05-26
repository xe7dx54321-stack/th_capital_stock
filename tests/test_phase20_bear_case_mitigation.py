import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_bear_case_mitigation import map_bear_case_to_evidence
from smr_claim_graph import ensure_claim_graph_tables, upsert_evidence
from smr_evidence_quality import ensure_evidence_quality_columns


def seed_evidence(conn, evidence_id: str, score: float) -> None:
    ensure_claim_graph_tables(conn)
    upsert_evidence(
        conn,
        {
            "evidence_id": evidence_id,
            "source_key": "cninfo_TEST",
            "source_type": "filing",
            "source_quality": "primary",
            "source_status": "active",
            "published_at": "2026-04-30",
            "ingested_at": "2026-04-30",
            "text_excerpt": "TEST.SZ revenue and gross profit from financial statement.",
            "metadata": {"ticker": "TEST.SZ", "chunk_section_type": "financial_statement"},
        },
    )
    ensure_evidence_quality_columns(conn)
    conn.execute(
        "UPDATE evidence_items SET quality_score=?, usable_for_core_claim=?, usable_for_promotion=? WHERE evidence_id=?",
        (score, 1 if score >= 0.55 else 0, 1 if score >= 0.68 else 0, evidence_id),
    )


class Phase20BearCaseMitigationTests(unittest.TestCase):
    def test_financial_statement_evidence_partially_mitigates_growth_risk(self):
        conn = sqlite3.connect(":memory:")
        seed_evidence(conn, "ev_revenue", 0.72)
        payload = map_bear_case_to_evidence(
            conn,
            ticker="TEST.SZ",
            primary_thesis_type="ai_infrastructure_demand",
            claims=[
                {
                    "bear_case_claim_id": "bear_growth",
                    "bear_case_text": "AI demand may not translate into revenue growth",
                    "risk_category": "growth_risk",
                    "core_to_thesis": True,
                }
            ],
            fundamentals_snapshot={
                "field_details": {
                    "revenue": {
                        "allowed_usage": "supporting_evidence",
                        "source_evidence_id": "ev_revenue",
                    }
                }
            },
        )

        response = payload["bear_case_mitigation"]["responses"][0]
        self.assertEqual(response["after_status"], "partially_mitigated")
        self.assertIn("ev_revenue", response["mitigating_evidence_ids"])

    def test_low_quality_evidence_cannot_mitigate_core_bear_case(self):
        conn = sqlite3.connect(":memory:")
        seed_evidence(conn, "ev_low", 0.2)
        payload = map_bear_case_to_evidence(
            conn,
            ticker="TEST.SZ",
            primary_thesis_type="ai_infrastructure_demand",
            claims=[
                {
                    "bear_case_claim_id": "bear_growth",
                    "bear_case_text": "revenue growth risk",
                    "risk_category": "growth_risk",
                    "core_to_thesis": True,
                }
            ],
            fundamentals_snapshot={
                "field_details": {
                    "revenue": {
                        "allowed_usage": "supporting_evidence",
                        "source_evidence_id": "ev_low",
                    }
                }
            },
        )

        response = payload["bear_case_mitigation"]["responses"][0]
        self.assertNotEqual(response["after_status"], "partially_mitigated")
        self.assertTrue(payload["bear_case_mitigation"]["blocks_pending"])

    def test_financial_statement_evidence_does_not_mitigate_direct_order_risk(self):
        conn = sqlite3.connect(":memory:")
        seed_evidence(conn, "ev_revenue", 0.72)
        payload = map_bear_case_to_evidence(
            conn,
            ticker="TEST.SZ",
            primary_thesis_type="ai_infrastructure_demand",
            claims=[
                {
                    "bear_case_claim_id": "bear_order",
                    "bear_case_text": "direct AI order evidence is missing",
                    "risk_category": "competitive_risk",
                    "core_to_thesis": True,
                }
            ],
            fundamentals_snapshot={
                "field_details": {
                    "revenue": {
                        "allowed_usage": "supporting_evidence",
                        "source_evidence_id": "ev_revenue",
                    }
                }
            },
        )

        response = payload["bear_case_mitigation"]["responses"][0]
        self.assertEqual(response["after_status"], "requires_more_evidence")
        self.assertEqual(response["mitigating_evidence_ids"], [])


if __name__ == "__main__":
    unittest.main()
