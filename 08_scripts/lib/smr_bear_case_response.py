#!/usr/bin/env python3
"""Structured responses to high bear-case claims."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class BearCaseResponse:
    ticker: str
    bear_case_claim_id: str | None
    bear_case_text: str
    response_status: str
    response_evidence_ids: list[str]
    response_summary: str
    action_effect: str
    confidence: float
    metadata: dict[str, Any]


VALID_RESPONSE_STATUSES = {"unresolved", "partially_mitigated", "mitigated", "not_applicable", "needs_manual_review"}
VALID_ACTION_EFFECTS = {
    "keep_status",
    "reduce_position_size",
    "downgrade_to_candidate_shadow",
    "downgrade_to_observation",
    "block_pending_review",
    "needs_manual_review",
}


def _quality_counts(evidence_rows: list[dict[str, Any]]) -> tuple[int, int]:
    live = 0
    usable = 0
    for row in evidence_rows:
        metadata = row.get("metadata") or {}
        if metadata.get("live") or row.get("source_type") in {"filing", "news", "fundamentals"}:
            live += 1
        if row.get("usable_for_promotion") or float(row.get("quality_score") or 0.0) >= 0.68:
            usable += 1
    return live, usable


def respond_to_bear_case(
    ticker: str,
    bear_case: dict[str, Any] | None,
    *,
    evidence_rows: list[dict[str, Any]] | None = None,
    fundamentals_snapshot: dict[str, Any] | None = None,
    valuation_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    bear_case = bear_case or {}
    evidence_rows = evidence_rows or []
    fundamentals_snapshot = fundamentals_snapshot or {}
    valuation_snapshot = valuation_snapshot or {}
    claims = bear_case.get("bear_case_claims") or []
    if not claims:
        return {
            "ticker": ticker,
            "overall_response_status": "not_applicable",
            "action_effect": "keep_status",
            "bear_case_responses": [],
            "summary": "no bear-case claims were generated",
        }

    live_count, usable_count = _quality_counts(evidence_rows)
    fundamentals_missing = fundamentals_snapshot.get("missing_fields") or []
    valuation_usage = valuation_snapshot.get("allowed_usage")
    responses: list[BearCaseResponse] = []
    for index, claim in enumerate(claims, start=1):
        text = str(claim.get("claim_text") or claim.get("text") or "")
        severity = str(claim.get("severity") or "medium").lower()
        evidence_ids = [row.get("evidence_id") for row in evidence_rows if row.get("evidence_id")][:3]
        if severity == "high" and (valuation_usage in {"context_only", "blocked_due_to_stale_price"} or len(fundamentals_missing) >= 3):
            status = "unresolved"
            action_effect = "block_pending_review"
            confidence = 0.25
            summary = "high bear case remains unresolved because valuation/data quality gates are still blocking"
            evidence_ids = []
        elif usable_count >= 2 and live_count >= 2 and len(fundamentals_missing) <= 2:
            status = "mitigated"
            action_effect = "keep_status"
            confidence = 0.72
            summary = "live evidence and fundamentals reduce the bear-case risk enough for normal review gates"
        elif usable_count >= 1 or live_count >= 2:
            status = "partially_mitigated"
            action_effect = "reduce_position_size"
            confidence = 0.58
            summary = "some live evidence mitigates the risk, but unresolved valuation/fundamentals gaps remain"
        else:
            status = "unresolved"
            action_effect = "block_pending_review"
            confidence = 0.3
            summary = "insufficient live evidence to answer the bear case"
            evidence_ids = []
        responses.append(
            BearCaseResponse(
                ticker=ticker,
                bear_case_claim_id=claim.get("claim_id"),
                bear_case_text=text,
                response_status=status,
                response_evidence_ids=[str(item) for item in evidence_ids if item],
                response_summary=summary,
                action_effect=action_effect,
                confidence=confidence,
                metadata={"claim_index": index, "claim_severity": severity},
            )
        )

    statuses = [item.response_status for item in responses]
    if any(status == "unresolved" for status in statuses):
        overall = "unresolved"
        action_effect = "block_pending_review"
    elif any(status == "partially_mitigated" for status in statuses):
        overall = "partially_mitigated"
        action_effect = "reduce_position_size"
    else:
        overall = "mitigated"
        action_effect = "keep_status"
    return {
        "ticker": ticker,
        "overall_response_status": overall,
        "action_effect": action_effect,
        "bear_case_responses": [asdict(item) for item in responses],
        "summary": "; ".join(item.response_summary for item in responses[:2]),
    }


def attach_bear_case_response(bear_case: dict[str, Any], response: dict[str, Any]) -> dict[str, Any]:
    updated = dict(bear_case or {})
    updated["bear_case_response"] = response
    if response.get("overall_response_status") == "mitigated":
        updated["thesis_response"] = response.get("summary")
    elif response.get("overall_response_status") == "partially_mitigated":
        updated["thesis_response"] = response.get("summary")
        updated["recommendation_adjustment"] = "reduce_position_or_wait"
    else:
        updated["thesis_response"] = None
        updated["recommendation_adjustment"] = "block_pending_review"
    return updated
