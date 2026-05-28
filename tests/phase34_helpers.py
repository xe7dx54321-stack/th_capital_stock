import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
TEST_DIR = ROOT / "tests"
for path in (LIB_DIR, TEST_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from phase31_helpers import phase31_candidate
from smr_controlled_review_plan import PHASE33_ACTOR, phase33_reason
from smr_evidence_review_actions import apply_evidence_review_action
from smr_semantic_evidence_persistence import write_semantic_evidence_candidates


def make_candidate(evidence_id: str, variable_type: str, *, ticker: str = "300394.SZ", usage: str = "scenario_analysis_only"):
    candidate = phase31_candidate(evidence_id, variable_type=variable_type, allowed_usage=usage)
    candidate["ticker"] = ticker
    candidate["source_id"] = f"source_{evidence_id}"
    candidate["chunk_id"] = f"chunk_{evidence_id}"
    candidate["quoted_span"] = f"{ticker} reviewed source text for {variable_type} {evidence_id}"
    candidate["claim_text"] = candidate["quoted_span"]
    return candidate


def make_phase34_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    write_semantic_evidence_candidates(
        conn,
        [
            make_candidate("ev_approved_capacity", "capacity_signal"),
            make_candidate("ev_downgraded_customer", "customer_allocation_signal", usage="context_only"),
            make_candidate("ev_rejected_end", "end_demand_signal"),
            make_candidate("ev_better_source", "ASP_price_signal"),
            make_candidate("ev_noise", "capacity_signal"),
        ],
    )
    apply_evidence_review_action(
        conn,
        evidence_id="ev_approved_capacity",
        action="approve_evidence",
        reason=phase33_reason("approve_evidence", "unit test approve without promotion"),
        actor=PHASE33_ACTOR,
        dry_run=False,
    )
    apply_evidence_review_action(
        conn,
        evidence_id="ev_downgraded_customer",
        action="downgrade_usage",
        target_usage="context_only",
        reason=phase33_reason("downgrade_usage", "unit test usage downgrade"),
        actor=PHASE33_ACTOR,
        dry_run=False,
    )
    apply_evidence_review_action(
        conn,
        evidence_id="ev_rejected_end",
        action="reject_evidence",
        reason=phase33_reason("reject_evidence", "unit test reject"),
        actor=PHASE33_ACTOR,
        dry_run=False,
    )
    apply_evidence_review_action(
        conn,
        evidence_id="ev_better_source",
        action="request_better_source",
        reason=phase33_reason("request_better_source", "unit test better source"),
        actor=PHASE33_ACTOR,
        dry_run=False,
    )
    apply_evidence_review_action(
        conn,
        evidence_id="ev_noise",
        action="mark_as_noise",
        reason=phase33_reason("mark_as_noise", "unit test noise"),
        actor=PHASE33_ACTOR,
        dry_run=False,
    )
    return conn
