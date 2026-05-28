import sqlite3
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
TEST_DIR = ROOT / "tests"
for path in (LIB_DIR, TEST_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from phase31_helpers import phase31_candidate
from smr_semantic_evidence_persistence import write_semantic_evidence_candidates


def phase37_candidate(evidence_id: str, variable_type: str, span: str, *, usage: str = "supporting_evidence") -> dict[str, Any]:
    candidate = phase31_candidate(evidence_id, variable_type=variable_type, allowed_usage=usage, quality_score=78)
    candidate["ticker"] = "300308.SZ"
    candidate["source_id"] = f"real_ir_300308_sz_{evidence_id}"
    candidate["source_url"] = f"https://static.cninfo.com.cn/finalpage/2026-05-{len(evidence_id):02d}/{evidence_id}.PDF"
    candidate["source_type"] = "investor_relations_record"
    candidate["chunk_id"] = f"chunk_{evidence_id}"
    candidate["quoted_span"] = span
    candidate["claim_text"] = span
    candidate["limitations"] = ["management commentary, not audited direct evidence"]
    candidate["payload"]["source_metadata"] = {
        "real_source": True,
        "section_type": "qa_section",
        "published_at": "2026-05-01",
    }
    return candidate


def make_phase37_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    write_semantic_evidence_candidates(
        conn,
        [
            phase37_candidate(
                "asp_mix",
                "ASP_price_signal",
                "800G 产品占比提升带动产品结构改善，但公司未披露精确 ASP。",
            ),
            phase37_candidate(
                "shipment",
                "shipment_signal",
                "公司表示 800G 和 1.6T 出货保持环比增长，交付节奏取决于客户订单量。",
            ),
            phase37_candidate(
                "order_visibility",
                "order_visibility_signal",
                "客户需求保持较快增长，公司会根据订单和物料准备情况安排交付。",
            ),
            phase37_candidate(
                "customer_proxy",
                "customer_allocation_signal",
                "海外大客户资本开支指引上调，但不代表公司获得确认客户分配。",
                usage="scenario_analysis_only",
            ),
        ],
    )
    return conn
