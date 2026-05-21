#!/usr/bin/env python3
"""Deterministic Bear Case Agent v2 for promotion-aware candidates."""

from __future__ import annotations

from typing import Any

from smr_claim_graph import _hash_id, ensure_claim_graph_tables, link_claim_evidence, upsert_claim


def _risk_level(condition: bool, fallback: str = "medium") -> str:
    return "high" if condition else fallback


def build_bear_case(
    conn,
    report_id: str,
    recommendation_id: str | None,
    dashboard_summary: dict[str, Any] | None = None,
    valuation_snapshot: dict[str, Any] | None = None,
    missing_data: list[dict[str, Any]] | list[str] | None = None,
    evidence_ids: list[str] | None = None,
) -> dict[str, Any]:
    ensure_claim_graph_tables(conn)
    summary = dashboard_summary or {}
    valuation = valuation_snapshot or {}
    missing = missing_data or []
    evidence_ids = evidence_ids or []
    action_text = str(summary.get("action_detail") or summary.get("action") or "")

    valuation_blocked = valuation.get("allowed_usage") in {"context_only", "blocked_due_to_stale_price"}
    missing_count = len(missing)
    data_quality_risk = _risk_level(missing_count >= 3 or valuation.get("allowed_usage") == "blocked_due_to_stale_price")
    valuation_risk = _risk_level(valuation_blocked)
    thesis_risk = "medium"
    timing_risk = "medium"

    bear_claims = []
    if valuation_blocked or valuation.get("valuation_status") in {"partial", "stale_price", "missing"}:
        bear_claims.append(
            {
                "claim_text": "Valuation evidence is incomplete; cheap/expensive language cannot be used as strong support.",
                "claim_type": "valuation_risk",
                "severity": valuation_risk,
                "what_would_confirm": "Forward EPS proxy, historical percentile, and peer comparison still support the thesis.",
            }
        )
    if missing:
        bear_claims.append(
            {
                "claim_text": "Key data gaps remain; expectation revision, industry-chain validation, or price validity may be insufficient.",
                "claim_type": "missing_data_risk",
                "severity": data_quality_risk,
                "what_would_confirm": "Missing data is repaired and still supports the original thesis.",
            }
        )
    if not bear_claims:
        bear_claims.append(
            {
                "claim_text": "The market may have already priced in the thesis, so price action and new primary evidence must keep confirming it.",
                "claim_type": "price_in_risk",
                "severity": "medium",
                "what_would_confirm": "Fresh filings/news continue to support the thesis without excessive price exhaustion.",
            }
        )

    deal_breakers = summary.get("kill_triggers") or [
        "Primary filing/news evidence no longer supports the core thesis.",
        "Margin or guidance deteriorates for two consecutive updates without a credible offset.",
        "The stock breaks the planned risk threshold before evidence improves.",
    ]
    evidence_backed_count = min(len(bear_claims), len(evidence_ids))
    high_count = sum(1 for claim in bear_claims if claim.get("severity") == "high")
    bear_case_strength = "high" if high_count else ("medium" if bear_claims else "low")
    inserted_claim_ids = []
    for index, claim in enumerate(bear_claims, start=1):
        claim_id = _hash_id("claim", report_id, recommendation_id, "bear", index, claim["claim_text"])
        upsert_claim(
            conn,
            {
                "claim_id": claim_id,
                "report_id": report_id,
                "recommendation_id": recommendation_id,
                "ticker": summary.get("ticker"),
                "theme": summary.get("theme"),
                "claim_text": claim["claim_text"],
                "claim_type": "bear_case",
                "importance": "supporting",
                "stance": "bear",
                "confidence": 0.55,
                "metadata": {**claim, "agent": "bear_case_v2"},
            },
        )
        inserted_claim_ids.append(claim_id)
        for evidence_id in evidence_ids[:2]:
            link_claim_evidence(conn, claim_id, evidence_id, "contextual", 0.45, "Bear Case v2 contextual evidence anchor.")
    adjustment = "reduce_position_or_wait" if action_text and bear_case_strength == "high" else ("observe" if not action_text else "normal_review")
    return {
        "bear_case_claims": bear_claims,
        "deal_breakers": deal_breakers,
        "recommendation_adjustment": adjustment,
        "claim_ids": inserted_claim_ids,
        "bear_case_strength": bear_case_strength,
        "deal_breaker_count": len(deal_breakers),
        "evidence_backed_bear_claim_count": evidence_backed_count,
        "valuation_risk": valuation_risk,
        "thesis_risk": thesis_risk,
        "timing_risk": timing_risk,
        "data_quality_risk": data_quality_risk,
        "alternative_explanation": "Observed signal could be price-in, temporary sentiment, or incomplete evidence rather than durable fundamental improvement.",
        "thesis_response": summary.get("bear_case_response"),
    }
