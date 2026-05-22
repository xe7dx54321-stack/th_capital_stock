#!/usr/bin/env python3
"""Explain why a live recommendation did or did not promote."""

from __future__ import annotations

from typing import Any


SEVERITY_BY_REQUIREMENT = {
    "daily_bar_fresh": "blocker",
    "news_not_globally_stale": "blocker",
    "relevant_filings_not_stale": "blocker",
    "consensus_proxy_quality": "blocker",
    "strong_proxy_or_official_consensus_for_pending_review": "blocker",
    "core_claim_evidence_quality": "blocker",
    "all_core_claims_supported": "blocker",
    "primary_evidence_for_fundamental_claims": "blocker",
    "fundamentals_snapshot_fresh_or_explainable": "blocker",
    "fresh_valuation_price": "blocker",
    "valuation_not_context_only_for_buy_add": "blocker",
    "data_quality_risk_not_high": "blocker",
}

FIX_HINTS = {
    "daily_bar_fresh": "backfill daily_bar/us_daily_bar to the latest expected trading session",
    "news_health": "run live news ingestion and inspect source-level freshness",
    "news_not_globally_stale": "repair at least one active live news source for the ticker/market",
    "relevant_filings_health": "run live filings ingestion for the ticker/watchlist",
    "relevant_filings_not_stale": "refresh ticker-level filings and export filing evidence",
    "consensus_proxy_quality": "extract primary guidance/revenue/EPS proxy signals from live evidence",
    "strong_proxy_or_official_consensus_for_pending_review": "add independent proxy signals or primary guidance evidence",
    "core_claim_evidence_quality": "replace administrative or stale evidence with high-quality live evidence",
    "all_core_claims_supported": "link every core claim to live evidence_id",
    "primary_evidence_for_fundamental_claims": "link at least one primary filing/fundamentals evidence item",
    "fundamentals_snapshot_fresh_or_explainable": "build ticker-level fundamentals with field-level missing reasons",
    "fresh_valuation_price": "refresh latest market price before valuation supports action",
    "valuation_not_context_only_for_buy_add": "add EPS/revenue/fundamentals support or keep recommendation as observation",
    "data_quality_risk_not_high": "repair fundamentals/evidence data quality or downgrade thesis",
}


def _priority(code: str, index: int) -> int:
    if code in {"daily_bar_fresh", "consensus_proxy_quality", "strong_proxy_or_official_consensus_for_pending_review"}:
        return 1
    if code in {"core_claim_evidence_quality", "primary_evidence_for_fundamental_claims", "fundamentals_snapshot_fresh_or_explainable"}:
        return 2
    if code.startswith("lint:"):
        return 3
    return index + 1


def explain_promotion_result(
    ticker: str,
    promotion_result: dict[str, Any],
    proxy: dict[str, Any] | None = None,
    fundamentals: dict[str, Any] | None = None,
    valuation: dict[str, Any] | None = None,
    evidence_check: dict[str, Any] | None = None,
    claim_graph: dict[str, Any] | None = None,
    data_health: dict[str, Any] | None = None,
) -> dict[str, Any]:
    proxy = proxy or {}
    fundamentals = fundamentals or {}
    valuation = valuation or {}
    evidence_check = evidence_check or {}
    claim_graph = claim_graph or {}
    data_health = data_health or {}
    missing = list(promotion_result.get("missing_requirements") or [])
    fixes = list(promotion_result.get("required_fixes") or [])
    blocking_factors = []
    for index, code in enumerate(missing):
        blocking_factors.append(
            {
                "code": code,
                "severity": SEVERITY_BY_REQUIREMENT.get(code, "warn" if code.startswith("lint:") else "blocker"),
                "fix_priority": _priority(code, index),
                "required_fix": FIX_HINTS.get(code) or (fixes[index] if index < len(fixes) else "inspect promotion snapshot"),
            }
        )
    near_pass_items = []
    if proxy.get("proxy_quality") in {"medium", "weak"}:
        near_pass_items.append(
            {
                "code": "PROXY_NEAR_PASS",
                "current": proxy.get("proxy_quality"),
                "needed": "strong",
                "detail": proxy.get("quality_reason") or "internal proxy exists but is not promotion grade",
            }
        )
    if valuation.get("allowed_usage") == "supporting_evidence":
        near_pass_items.append(
            {
                "code": "VALUATION_SUPPORTING_ONLY",
                "current": "supporting_evidence",
                "needed": "promotion_eligible",
                "detail": "valuation can support context but lacks full promotion-grade forward/peer support",
            }
        )
    if fundamentals.get("freshness_status") == "degraded":
        near_pass_items.append(
            {
                "code": "FUNDAMENTALS_DEGRADED",
                "current": "degraded",
                "needed": "fresh or explainable_missing",
                "detail": ", ".join(fundamentals.get("missing_fields") or [])[:240],
            }
        )
    minimum_fix_path = []
    for factor in sorted(blocking_factors, key=lambda item: item["fix_priority"]):
        fix = factor["required_fix"]
        if fix not in minimum_fix_path:
            minimum_fix_path.append(fix)
        if len(minimum_fix_path) >= 5:
            break
    if not minimum_fix_path and promotion_result.get("allowed"):
        minimum_fix_path.append("no blocker; item is eligible for pending_human_review")
    return {
        "ticker": ticker,
        "current_status": promotion_result.get("from_status") or "observation_only",
        "target_status": "pending_human_review",
        "promotion_allowed": bool(promotion_result.get("allowed")),
        "blocking_factors": blocking_factors,
        "near_pass_items": near_pass_items,
        "minimum_fix_path": minimum_fix_path,
        "snapshots": {
            "proxy_quality": proxy.get("proxy_quality"),
            "proxy_signal_count": proxy.get("proxy_signal_count"),
            "fundamentals_status": fundamentals.get("freshness_status"),
            "fundamentals_missing_fields": fundamentals.get("missing_fields") or [],
            "valuation_usage": valuation.get("allowed_usage"),
            "evidence_summary": evidence_check.get("evidence_summary") or {},
            "unsupported_core_claims": claim_graph.get("unsupported_core_claims") or [],
            "data_health_overall": data_health.get("overall_status"),
        },
    }
