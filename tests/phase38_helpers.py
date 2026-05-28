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


def _candidate(evidence_id: str, variable_type: str, span: str, *, usage: str = "supporting_evidence") -> dict[str, Any]:
    candidate = phase31_candidate(evidence_id, variable_type=variable_type, allowed_usage=usage, quality_score=78)
    candidate["ticker"] = "300308.SZ"
    candidate["source_id"] = f"phase38_source_{evidence_id}"
    candidate["source_url"] = f"https://example.com/phase38/{evidence_id}.pdf"
    candidate["source_type"] = "investor_relations_record"
    candidate["chunk_id"] = f"chunk_{evidence_id}"
    candidate["quoted_span"] = span
    candidate["claim_text"] = span
    candidate["limitations"] = ["management commentary", "not confirmed allocation"]
    candidate["payload"]["source_metadata"] = {
        "real_source": True,
        "section_type": "qa_section",
        "published_at": "2026-05-01",
    }
    candidate["payload"]["gate"]["extraction"] = {
        "evidence_strength": "management_commentary",
        "is_company_specific": True,
        "risk_flags": ["management_commentary"],
    }
    return candidate


def make_phase38_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    rows = []
    for index in range(3):
        rows.append(
            _candidate(
                f"asp_mix_{index}",
                "ASP_price_signal",
                f"Management said 800G product mix and gross margin improved in quarter {index}, while exact commercial terms were not disclosed.",
            )
        )
        rows.append(
            _candidate(
                f"order_{index}",
                "order_visibility_signal",
                f"Management said order backlog and customer demand visibility supported delivery planning in quarter {index}.",
            )
        )
        rows.append(
            _candidate(
                f"shipment_{index}",
                "shipment_signal",
                f"Management said shipment and delivery volumes for 800G products improved sequentially in quarter {index}.",
            )
        )
        rows.append(
            _candidate(
                f"customer_{index}",
                "customer_allocation_signal",
                f"Management discussed overseas customer demand and allocation uncertainty in quarter {index}, without confirmed allocation.",
                usage="scenario_analysis_only",
            )
        )
    write_semantic_evidence_candidates(conn, rows)
    return conn
