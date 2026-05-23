#!/usr/bin/env python3
"""Stable blocker taxonomy for live reliability triage.

Phase 8 turns repeated free-form blocker messages into repairable work items.
This module is intentionally deterministic: it only normalizes existing
promotion, evidence, fundamentals, and portfolio-risk blockers.
"""

from __future__ import annotations

from typing import Any


STABLE_BLOCKER_CODES = {
    "FUNDAMENTALS_MISSING_FIELDS",
    "FILING_FRESHNESS_DEGRADED",
    "LIVE_NEWS_MISSING",
    "PROXY_WEAK",
    "PROXY_INVALID",
    "VALUATION_CONTEXT_ONLY",
    "VALUATION_NOT_PROMOTION_ELIGIBLE",
    "HIGH_BEAR_CASE",
    "DATA_QUALITY_RISK",
    "EVIDENCE_QUALITY_LOW",
    "PRIMARY_EVIDENCE_MISSING",
    "COUNTER_EVIDENCE_MISSING",
    "RISK_LIMIT_EXCEEDED",
    "THEME_EXPOSURE_LIMIT",
    "SECTOR_EXPOSURE_LIMIT",
    "MARKET_EXPOSURE_LIMIT",
    "LIQUIDITY_RISK",
    "UNKNOWN_BLOCKER",
}

CODE_ALIASES = {
    "fundamentals_snapshot": "FUNDAMENTALS_MISSING_FIELDS",
    "fundamentals_snapshot_fresh_or_explainable": "FUNDAMENTALS_MISSING_FIELDS",
    "fundamentals_degraded": "FUNDAMENTALS_MISSING_FIELDS",
    "fundamentals_missing": "FUNDAMENTALS_MISSING_FIELDS",
    "relevant_filings_health": "FILING_FRESHNESS_DEGRADED",
    "relevant_filings_not_stale": "FILING_FRESHNESS_DEGRADED",
    "filing_freshness_degraded": "FILING_FRESHNESS_DEGRADED",
    "news_health": "LIVE_NEWS_MISSING",
    "news_not_globally_stale": "LIVE_NEWS_MISSING",
    "live_news_missing": "LIVE_NEWS_MISSING",
    "consensus_proxy_quality": "PROXY_INVALID",
    "strong_proxy_or_official_consensus_for_pending_review": "PROXY_INVALID",
    "proxy_near_pass": "PROXY_WEAK",
    "fresh_valuation_price": "VALUATION_NOT_PROMOTION_ELIGIBLE",
    "valuation_supporting_only": "VALUATION_NOT_PROMOTION_ELIGIBLE",
    "valuation_not_context_only_for_buy_add": "VALUATION_CONTEXT_ONLY",
    "daily_bar_fresh": "DATA_QUALITY_RISK",
    "data_health_snapshot": "DATA_QUALITY_RISK",
    "data_quality_risk_not_high": "DATA_QUALITY_RISK",
    "no_block_level_source_issue": "DATA_QUALITY_RISK",
    "core_claim_evidence_quality": "EVIDENCE_QUALITY_LOW",
    "two_independent_evidence_sources": "EVIDENCE_QUALITY_LOW",
    "all_core_claims_supported": "EVIDENCE_QUALITY_LOW",
    "primary_evidence_for_fundamental_claims": "PRIMARY_EVIDENCE_MISSING",
    "counter_evidence": "COUNTER_EVIDENCE_MISSING",
    "counter_evidence_missing": "COUNTER_EVIDENCE_MISSING",
    "high_bear_case": "HIGH_BEAR_CASE",
    "high_bear_case_answered": "HIGH_BEAR_CASE",
    "risk_headroom": "RISK_LIMIT_EXCEEDED",
    "daily_new_position_limit": "RISK_LIMIT_EXCEEDED",
    "single_name_exposure": "RISK_LIMIT_EXCEEDED",
    "theme_exposure": "THEME_EXPOSURE_LIMIT",
    "sector_exposure": "SECTOR_EXPOSURE_LIMIT",
    "market_exposure": "MARKET_EXPOSURE_LIMIT",
    "liquidity": "LIQUIDITY_RISK",
    "liquidity_risk": "LIQUIDITY_RISK",
}

BLOCKER_TYPES = {
    "FUNDAMENTALS_MISSING_FIELDS": "fundamentals",
    "FILING_FRESHNESS_DEGRADED": "filings",
    "LIVE_NEWS_MISSING": "news",
    "PROXY_WEAK": "proxy",
    "PROXY_INVALID": "proxy",
    "VALUATION_CONTEXT_ONLY": "valuation",
    "VALUATION_NOT_PROMOTION_ELIGIBLE": "valuation",
    "HIGH_BEAR_CASE": "risk",
    "DATA_QUALITY_RISK": "data_quality",
    "EVIDENCE_QUALITY_LOW": "evidence",
    "PRIMARY_EVIDENCE_MISSING": "evidence",
    "COUNTER_EVIDENCE_MISSING": "evidence",
    "RISK_LIMIT_EXCEEDED": "portfolio_risk",
    "THEME_EXPOSURE_LIMIT": "portfolio_risk",
    "SECTOR_EXPOSURE_LIMIT": "portfolio_risk",
    "MARKET_EXPOSURE_LIMIT": "portfolio_risk",
    "LIQUIDITY_RISK": "portfolio_risk",
    "UNKNOWN_BLOCKER": "unknown",
}

DEFAULT_SEVERITY = {
    "FUNDAMENTALS_MISSING_FIELDS": "high",
    "FILING_FRESHNESS_DEGRADED": "high",
    "LIVE_NEWS_MISSING": "high",
    "PROXY_WEAK": "medium",
    "PROXY_INVALID": "high",
    "VALUATION_CONTEXT_ONLY": "medium",
    "VALUATION_NOT_PROMOTION_ELIGIBLE": "high",
    "HIGH_BEAR_CASE": "high",
    "DATA_QUALITY_RISK": "high",
    "EVIDENCE_QUALITY_LOW": "high",
    "PRIMARY_EVIDENCE_MISSING": "high",
    "COUNTER_EVIDENCE_MISSING": "medium",
    "RISK_LIMIT_EXCEEDED": "high",
    "THEME_EXPOSURE_LIMIT": "high",
    "SECTOR_EXPOSURE_LIMIT": "high",
    "MARKET_EXPOSURE_LIMIT": "high",
    "LIQUIDITY_RISK": "high",
    "UNKNOWN_BLOCKER": "medium",
}

DEFAULT_FIXABILITY = {
    "FUNDAMENTALS_MISSING_FIELDS": "medium",
    "FILING_FRESHNESS_DEGRADED": "medium",
    "LIVE_NEWS_MISSING": "medium",
    "PROXY_WEAK": "medium",
    "PROXY_INVALID": "medium",
    "VALUATION_CONTEXT_ONLY": "medium",
    "VALUATION_NOT_PROMOTION_ELIGIBLE": "medium",
    "HIGH_BEAR_CASE": "low",
    "DATA_QUALITY_RISK": "medium",
    "EVIDENCE_QUALITY_LOW": "medium",
    "PRIMARY_EVIDENCE_MISSING": "medium",
    "COUNTER_EVIDENCE_MISSING": "medium",
    "RISK_LIMIT_EXCEEDED": "high",
    "THEME_EXPOSURE_LIMIT": "high",
    "SECTOR_EXPOSURE_LIMIT": "high",
    "MARKET_EXPOSURE_LIMIT": "high",
    "LIQUIDITY_RISK": "medium",
    "UNKNOWN_BLOCKER": "low",
}

SUGGESTED_FIX = {
    "FUNDAMENTALS_MISSING_FIELDS": "improve financial table extraction and persist field-level evidence with missing_reason",
    "FILING_FRESHNESS_DEGRADED": "refresh live filings ingestion and ensure primary filing evidence is exported",
    "LIVE_NEWS_MISSING": "repair live news ingestion and source freshness for the ticker/market",
    "PROXY_WEAK": "add an independent primary or high-quality secondary proxy signal",
    "PROXY_INVALID": "extract guidance, revenue, EPS, or target-revision proxy signals from live evidence",
    "VALUATION_CONTEXT_ONLY": "recompute valuation after fundamentals/proxy evidence improves",
    "VALUATION_NOT_PROMOTION_ELIGIBLE": "refresh price and fundamentals so valuation can support promotion",
    "HIGH_BEAR_CASE": "address deal-breaker risk or keep the item below pending review",
    "DATA_QUALITY_RISK": "repair freshness or source-quality issues before promotion",
    "EVIDENCE_QUALITY_LOW": "replace low-relevance evidence with high-quality live evidence",
    "PRIMARY_EVIDENCE_MISSING": "link at least one primary filing or fundamentals evidence item",
    "COUNTER_EVIDENCE_MISSING": "add counter-evidence or bear-case evidence before promotion",
    "RISK_LIMIT_EXCEEDED": "reduce candidate size or wait for portfolio exposure headroom",
    "THEME_EXPOSURE_LIMIT": "reduce same-theme exposure or downsize the candidate",
    "SECTOR_EXPOSURE_LIMIT": "reduce same-sector exposure or downsize the candidate",
    "MARKET_EXPOSURE_LIMIT": "reduce same-market exposure or downsize the candidate",
    "LIQUIDITY_RISK": "verify liquidity and price freshness before sizing",
    "UNKNOWN_BLOCKER": "inspect raw blocker and add a stable taxonomy mapping",
}

EXPECTED_IMPACT = {
    "FUNDAMENTALS_MISSING_FIELDS": "may_upgrade_candidate_shadow_to_pending_review",
    "FILING_FRESHNESS_DEGRADED": "may_restore_primary_evidence_gate",
    "LIVE_NEWS_MISSING": "may_restore_live_evidence_gate",
    "PROXY_WEAK": "may_upgrade_proxy_to_promotion_grade",
    "PROXY_INVALID": "may_upgrade_proxy_to_promotion_grade",
    "VALUATION_CONTEXT_ONLY": "may_upgrade_valuation_to_supporting_or_promotion_eligible",
    "VALUATION_NOT_PROMOTION_ELIGIBLE": "may_restore_valuation_gate",
    "HIGH_BEAR_CASE": "may_keep_candidate_shadow_until_risk_is_answered",
    "DATA_QUALITY_RISK": "may_restore_data_quality_gate",
    "EVIDENCE_QUALITY_LOW": "may_restore_core_claim_support",
    "PRIMARY_EVIDENCE_MISSING": "may_restore_fundamental_claim_support",
    "COUNTER_EVIDENCE_MISSING": "may_restore_bear_case_gate",
    "RISK_LIMIT_EXCEEDED": "may_downsize_or_hold_candidate",
    "THEME_EXPOSURE_LIMIT": "may_downsize_or_hold_candidate",
    "SECTOR_EXPOSURE_LIMIT": "may_downsize_or_hold_candidate",
    "MARKET_EXPOSURE_LIMIT": "may_downsize_or_hold_candidate",
    "LIQUIDITY_RISK": "may_block_execution_until_liquidity_verified",
    "UNKNOWN_BLOCKER": "requires_manual_triage",
}


def _clean_code(value: Any) -> str:
    return str(value or "").strip()


def _canonical_key(value: Any) -> str:
    return _clean_code(value).lower().replace(" ", "_").replace("-", "_")


def _normalize_severity(value: Any, fallback: str) -> str:
    raw = str(value or "").strip().lower()
    if raw in {"block", "blocked", "blocker", "critical", "high"}:
        return "high"
    if raw in {"warn", "warning", "medium"}:
        return "medium"
    if raw in {"info", "low"}:
        return "low"
    return fallback


def stable_blocker_code(raw_code: Any, context: dict[str, Any] | None = None) -> str:
    context = context or {}
    raw = _clean_code(raw_code)
    if raw in STABLE_BLOCKER_CODES:
        return raw
    key = _canonical_key(raw)
    if key in {"consensus_proxy_quality", "strong_proxy_or_official_consensus_for_pending_review"}:
        proxy_quality = str(context.get("proxy_quality") or "").lower()
        return "PROXY_WEAK" if proxy_quality == "weak" else "PROXY_INVALID"
    if key.startswith("lint:"):
        return "EVIDENCE_QUALITY_LOW"
    return CODE_ALIASES.get(key, "UNKNOWN_BLOCKER")


def normalize_blocker(blocker: Any, context: dict[str, Any] | None = None) -> dict[str, Any]:
    context = context or {}
    raw: dict[str, Any]
    if isinstance(blocker, dict):
        raw = dict(blocker)
        raw_code = raw.get("code") or raw.get("blocker_code") or raw.get("detail") or raw.get("message")
    else:
        raw = {"message": str(blocker)}
        raw_code = blocker
    code = stable_blocker_code(raw_code, context)
    affected_fields = raw.get("affected_fields") or []
    if code == "FUNDAMENTALS_MISSING_FIELDS" and not affected_fields:
        affected_fields = (
            context.get("fundamentals_missing_fields")
            or context.get("missing_fields")
            or raw.get("missing_fields")
            or []
        )
    if isinstance(affected_fields, str):
        affected_fields = [item.strip() for item in affected_fields.split(",") if item.strip()]
    raw_message = raw.get("message") or raw.get("detail") or raw.get("required_fix") or raw.get("raw_message") or _clean_code(raw_code)
    suggested_fix = raw.get("suggested_fix") or raw.get("required_fix") or SUGGESTED_FIX[code]
    return {
        "code": code,
        "type": raw.get("type") or raw.get("blocker_type") or BLOCKER_TYPES[code],
        "severity": _normalize_severity(raw.get("severity"), DEFAULT_SEVERITY[code]),
        "fixability": raw.get("fixability") or DEFAULT_FIXABILITY[code],
        "message": raw_message,
        "affected_fields": list(dict.fromkeys(str(item) for item in affected_fields if str(item).strip())),
        "suggested_fix": suggested_fix,
        "expected_impact": raw.get("expected_impact") or EXPECTED_IMPACT[code],
        "raw_code": _clean_code(raw_code),
        "raw_message": raw_message,
    }


def normalize_blockers(blockers: list[Any] | None, context: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for item in blockers or []:
        blocker = normalize_blocker(item, context=context)
        key = (blocker["code"], ",".join(blocker.get("affected_fields") or []))
        if key in seen:
            continue
        seen.add(key)
        normalized.append(blocker)
    return normalized


def minimum_fix_path_from_blockers(blockers: list[dict[str, Any]], limit: int = 5) -> list[dict[str, str]]:
    path: list[dict[str, str]] = []
    seen: set[str] = set()
    for blocker in blockers:
        code = str(blocker.get("code") or "UNKNOWN_BLOCKER")
        fix = str(blocker.get("suggested_fix") or SUGGESTED_FIX.get(code) or SUGGESTED_FIX["UNKNOWN_BLOCKER"])
        if code in seen:
            continue
        seen.add(code)
        path.append({"code": code, "fix": fix})
        if len(path) >= limit:
            break
    return path


def priority_for_blocker(blocker: dict[str, Any]) -> str:
    severity = str(blocker.get("severity") or "").lower()
    fixability = str(blocker.get("fixability") or "").lower()
    if severity == "high" and fixability in {"high", "medium"}:
        return "high"
    if severity == "high":
        return "medium"
    if severity == "medium" and fixability in {"high", "medium"}:
        return "medium"
    return "low"
