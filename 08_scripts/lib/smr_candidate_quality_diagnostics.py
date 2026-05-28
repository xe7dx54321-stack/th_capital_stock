#!/usr/bin/env python3
"""Phase 51 candidate quality diagnostics — analyze downgrade reasons."""
from __future__ import annotations
from typing import Any
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts

DOWNGRADE_REASONS = [
    "fixture_source_penalty", "metadata_derived_penalty", "quoted_span_weak",
    "chunk_type_generic", "source_traceability_weak", "sensitive_variable_guard",
    "claim_strength_weak", "title_only_chunk"
]

def diagnose_candidate(candidate):
    reasons = []
    cid = candidate.get("candidate_id", "")
    var = candidate.get("variable", "")
    quoted = candidate.get("quoted_span", "")
    source_id = candidate.get("source_id", "")
    chunk_id = candidate.get("chunk_id", "")

    # Fixture / metadata penalties
    if "cninfo" in (source_id or ""):
        reasons.append("fixture_source_penalty")
    if len(quoted or "") < 60:
        reasons.append("quoted_span_weak")
    if candidate.get("chunk_type", "") in ("unknown", "general_text"):
        reasons.append("chunk_type_generic")
    if not source_id:
        reasons.append("source_traceability_weak")
    if var in ("supplier_share_scenario", "customer_allocation_proxy", "official_consensus_status"):
        reasons.append("sensitive_variable_guard")
    if candidate.get("confidence", "medium") == "low":
        reasons.append("claim_strength_weak")

    upgrade = "low"
    if len(reasons) <= 1: upgrade = "high"
    elif len(reasons) <= 2: upgrade = "medium"
    else: upgrade = "low"

    s_score = 0.8 if source_id else 0.2
    q_score = 0.7 if len(quoted or "") >= 60 else 0.35
    ck_score = 0.7 if candidate.get("chunk_type", "") not in ("unknown", "general_text") else 0.3
    cl_score = 0.7 if candidate.get("confidence", "medium") != "low" else 0.3

    return {
        "candidate_id": cid, "variable": var, "source_id": source_id,
        "chunk_id": chunk_id, "chunk_type": candidate.get("chunk_type", "unknown"),
        "quality_status_before": "downgraded",
        "downgrade_reasons": reasons,
        "source_traceability_score": round(s_score, 2),
        "quoted_span_score": round(q_score, 2),
        "chunk_quality_score": round(ck_score, 2),
        "claim_strength_score": round(cl_score, 2),
        "upgrade_potential": upgrade,
        "recommended_fix": _recommend_fix(reasons)
    }

def _recommend_fix(reasons):
    if not reasons: return "no fix needed"
    if "fixture_source_penalty" in reasons: return "replace fixture with real source text"
    if "quoted_span_weak" in reasons: return "improve quoted_span specificity and length"
    if "chunk_type_generic" in reasons: return "improve chunk type classification"
    return "address: " + ", ".join(reasons)

def build_diagnostics(candidates, ticker=TARGET_REVIEW_TICKER):
    rows = [diagnose_candidate(c) for c in candidates]
    d_reasons = {}
    for r in rows:
        for reason in r["downgrade_reasons"]:
            d_reasons[reason] = d_reasons.get(reason, 0) + 1
    return {
        "ticker": normalize_ticker(ticker),
        "candidate_quality_diagnostics": {
            "candidates_checked": len(candidates),
            "downgraded_before": len(rows),
            "upgrade_potential_high": sum(1 for r in rows if r["upgrade_potential"] == "high"),
            "upgrade_potential_medium": sum(1 for r in rows if r["upgrade_potential"] == "medium"),
            "upgrade_potential_low": sum(1 for r in rows if r["upgrade_potential"] == "low"),
            "top_downgrade_reasons": d_reasons,
            "rows": rows,
            "pending_created": 0, "paper_order_created": 0
        }
    }
