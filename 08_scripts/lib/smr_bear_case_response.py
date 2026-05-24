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


def _valuation_support_evidence(ticker: str, valuation_snapshot: dict[str, Any]) -> list[str]:
    generated_at = str(valuation_snapshot.get("generated_at") or "").replace(" ", "_").replace(":", "")
    suffix = generated_at or "latest"
    evidence = []
    peer = valuation_snapshot.get("peer_comparison") or {}
    historical = valuation_snapshot.get("historical_valuation") or {}
    if peer.get("peer_comparison_status") in {"supporting", "promotion_supporting"}:
        evidence.append(f"valuation_peer_snapshot_{ticker}_{suffix}")
    if historical.get("status") in {"partial", "available"}:
        evidence.append(f"historical_valuation_{ticker}_{suffix}")
    return evidence


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
        valuation_blocked = valuation_usage in {"context_only", "blocked_due_to_stale_price"}
        core_valuation_risk = any(token in text.lower() for token in ("valuation", "rerating", "multiple", "price"))
        valuation_evidence_ids = _valuation_support_evidence(ticker, valuation_snapshot)
        if severity == "high" and core_valuation_risk and valuation_blocked:
            status = "unresolved"
            action_effect = "block_pending_review"
            confidence = 0.25
            summary = "high bear case remains unresolved because valuation/data quality gates are still blocking"
            evidence_ids = []
        elif severity == "high" and core_valuation_risk and valuation_evidence_ids:
            status = "partially_mitigated"
            action_effect = "reduce_position_size"
            confidence = 0.61
            summary = "peer or historical valuation support partially addresses valuation rerating risk, but it remains supporting-only"
            evidence_ids = valuation_evidence_ids[:3]
        elif severity == "high" and (valuation_blocked or len(fundamentals_missing) >= 3) and (usable_count >= 1 or live_count >= 2):
            status = "partially_mitigated"
            action_effect = "reduce_position_size"
            confidence = 0.56
            summary = "live evidence addresses part of the risk, but valuation or fundamentals gaps still prevent pending review"
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
    unresolved_count = sum(1 for status in statuses if status == "unresolved")
    partially_mitigated_count = sum(1 for status in statuses if status == "partially_mitigated")
    mitigated_count = sum(1 for status in statuses if status == "mitigated")
    if unresolved_count:
        overall = "unresolved"
        action_effect = "block_pending_review"
    elif partially_mitigated_count:
        overall = "partially_mitigated"
        action_effect = "reduce_position_size"
    else:
        overall = "mitigated"
        action_effect = "keep_status"
    return {
        "ticker": ticker,
        "overall_response_status": overall,
        "bear_case_response_summary": {
            "overall_status": overall,
            "unresolved_count": unresolved_count,
            "partially_mitigated_count": partially_mitigated_count,
            "mitigated_count": mitigated_count,
            "action_effect": action_effect,
        },
        "action_effect": action_effect,
        "bear_case_responses": [asdict(item) for item in responses],
        "responses": [asdict(item) for item in responses],
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
