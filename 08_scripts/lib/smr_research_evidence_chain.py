#!/usr/bin/env python3
"""Phase 35 evidence-chain organization for single-stock research packets."""

from __future__ import annotations

import sqlite3
from typing import Any

from smr_evidence_lifecycle import list_lifecycle_states, list_semantic_evidence_candidates, loads_json
from smr_evidence_review_workbench import COMPANY_NAMES
from smr_post_governance_evidence_state import INACTIVE_LIFECYCLE_STATUSES, normalize_research_variable
from smr_supplier_exposure_model import get_supplier_exposure_profile
from smr_wiki import now_ts


REJECTED_OR_NOISE_STATUSES = {"rejected_evidence", "marked_noise", "removed", "archived"}


def _payload(candidate: dict[str, Any]) -> dict[str, Any]:
    value = candidate.get("payload")
    if isinstance(value, dict):
        return value
    return loads_json(candidate.get("payload_json"), {})


def _quality(candidate: dict[str, Any], state: dict[str, Any]) -> tuple[int | None, str]:
    payload = _payload(candidate)
    quality = candidate.get("quality") or payload.get("quality") or {}
    score = state.get("quality_score")
    if score is None:
        score = quality.get("quality_score")
    bucket = state.get("quality_bucket") or quality.get("quality_bucket")
    if bucket:
        bucket = str(bucket)
    elif score is not None and str(score).isdigit() and int(score) >= 70:
        bucket = "usable"
    else:
        bucket = "partial"
    try:
        score_int = int(score) if score is not None else None
    except (TypeError, ValueError):
        score_int = None
    return score_int, bucket


def _review_status(lifecycle_status: str, review_status: str | None) -> str:
    mapping = {
        "approved_evidence": "approved",
        "downgraded_evidence": "downgraded",
        "rejected_evidence": "rejected",
        "marked_noise": "noise",
        "needs_better_source": "needs_better_source",
        "linked_to_variable_pack": "linked",
    }
    if lifecycle_status in mapping:
        return mapping[lifecycle_status]
    if review_status == "reviewed":
        return "reviewed"
    if review_status == "review_required":
        return "review_required"
    return "not_reviewed"


def _evidence_quality(bucket: str, score: int | None, lifecycle_status: str) -> str:
    if lifecycle_status in {"rejected_evidence", "marked_noise"}:
        return "inactive"
    if lifecycle_status == "downgraded_evidence":
        return "downgraded"
    if bucket in {"usable", "strong"} or (score is not None and score >= 70):
        return "usable"
    if bucket in {"review_required", "weak_but_usable"}:
        return "review_required"
    return "partial"


def _sort_key(row: dict[str, Any]) -> tuple[int, int, int, str]:
    status_rank = {
        "approved": 0,
        "linked": 1,
        "downgraded": 2,
        "not_reviewed": 3,
        "needs_better_source": 4,
        "review_required": 5,
    }.get(str(row.get("review_status")), 6)
    quality_rank = 0 if row.get("evidence_quality") == "usable" else 1
    usage_rank = 0 if row.get("allowed_usage") != "context_only" else 1
    return (status_rank, quality_rank, usage_rank, str(row.get("evidence_id") or ""))


def build_research_evidence_chain(conn: sqlite3.Connection, ticker: str, *, limit: int = 12) -> dict[str, Any]:
    """Return a ticker-level evidence-chain packet without changing state."""

    ticker = str(ticker or "").strip().upper()
    profile = get_supplier_exposure_profile(ticker)
    candidates = list_semantic_evidence_candidates(conn, ticker=ticker)
    states = {str(row.get("evidence_id")): row for row in list_lifecycle_states(conn, ticker=ticker)}
    rows: list[dict[str, Any]] = []
    for candidate in candidates:
        evidence_id = str(candidate.get("evidence_id") or "")
        state = states.get(evidence_id) or {}
        lifecycle_status = str(state.get("lifecycle_status") or "persisted_candidate")
        review_status = _review_status(lifecycle_status, state.get("review_status"))
        score, bucket = _quality(candidate, state)
        variable = normalize_research_variable(candidate.get("variable_type"))
        row = {
            "evidence_id": evidence_id,
            "source_id": candidate.get("source_id") or state.get("source_id"),
            "source_url": candidate.get("source_url") or state.get("source_url"),
            "source_type": candidate.get("source_type") or (state.get("metadata") or {}).get("source_type"),
            "topic": variable,
            "variable_type": candidate.get("variable_type") or state.get("variable_type"),
            "allowed_usage": state.get("allowed_usage") or candidate.get("allowed_usage"),
            "lifecycle_status": lifecycle_status,
            "review_status": review_status,
            "quality_score": score,
            "quality_bucket": bucket,
            "evidence_quality": _evidence_quality(bucket, score, lifecycle_status),
            "quoted_span": candidate.get("quoted_span") or state.get("quoted_span_preview"),
            "claim_text": candidate.get("claim_text"),
            "active_for_research": lifecycle_status not in INACTIVE_LIFECYCLE_STATUSES,
            "usable_for_promotion": False,
        }
        rows.append(row)

    key_candidates = [
        row
        for row in rows
        if row.get("active_for_research")
        and row.get("lifecycle_status") not in REJECTED_OR_NOISE_STATUSES
        and row.get("source_url")
        and row.get("quoted_span")
    ]
    key_evidence = sorted(key_candidates, key=_sort_key)[: max(0, int(limit))]
    chain = {
        "total_evidence": len(rows),
        "reviewed_evidence": sum(1 for row in rows if row.get("review_status") not in {"not_reviewed", "review_required"}),
        "approved_evidence": sum(1 for row in rows if row.get("lifecycle_status") == "approved_evidence"),
        "downgraded_evidence": sum(1 for row in rows if row.get("lifecycle_status") == "downgraded_evidence"),
        "rejected_evidence": sum(1 for row in rows if row.get("lifecycle_status") == "rejected_evidence"),
        "marked_noise": sum(1 for row in rows if row.get("lifecycle_status") == "marked_noise"),
        "high_quality_evidence": sum(1 for row in rows if row.get("active_for_research") and row.get("evidence_quality") == "usable"),
        "context_only_evidence": sum(1 for row in rows if row.get("allowed_usage") == "context_only"),
        "review_required": sum(1 for row in rows if row.get("review_status") == "review_required"),
        "key_evidence": key_evidence,
    }
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "company_name": profile.get("company_name") or COMPANY_NAMES.get(ticker),
        "evidence_chain": chain,
        "safety": {
            "rejected_or_noise_in_key_evidence": any(
                row.get("lifecycle_status") in REJECTED_OR_NOISE_STATUSES for row in key_evidence
            ),
            "evidence_chain_is_thesis_conclusion": False,
            "promotion_allowed": False,
        },
    }
