import sqlite3
from typing import Any

from smr_semantic_evidence_persistence import write_semantic_evidence_candidates


def phase31_candidate(
    evidence_id: str = "ev_semantic_ir_test",
    *,
    variable_type: str = "capacity_signal",
    allowed_usage: str = "scenario_analysis_only",
    quality_bucket: str = "usable",
    quality_score: int = 74,
) -> dict[str, Any]:
    span = "答：公司持续推进高速光器件相关产能建设，并根据客户需求节奏安排交付。"
    return {
        "evidence_id": evidence_id,
        "ticker": "300394.SZ",
        "theme": "ai_optical_interconnect",
        "source_id": "ir_300394_sz_test_001",
        "source_url": "https://static.cninfo.com.cn/test.pdf",
        "source_type": "investor_relations_record",
        "chunk_id": "chunk_0001",
        "quoted_span": span,
        "variable_type": variable_type,
        "claim_text": span,
        "evidence_status": "partial",
        "allowed_usage": allowed_usage,
        "usable_for_expectation_gap": True,
        "usable_for_valuation_support": False,
        "usable_for_promotion": False,
        "limitations": ["management commentary", "not quantified"],
        "payload": {
            "source_metadata": {"real_source": True, "section_type": "qa_section", "published_at": "2026-05-01"},
            "gate": {"extraction": {"evidence_strength": "management_commentary", "is_company_specific": True}},
            "quality": {
                "quality_score": quality_score,
                "quality_bucket": quality_bucket,
                "noise": {"noise_detected": False, "noise_types": [], "recommended_action": "keep"},
            },
        },
    }


def make_conn_with_candidate(candidate: dict[str, Any] | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    write_semantic_evidence_candidates(conn, [candidate or phase31_candidate()])
    return conn
