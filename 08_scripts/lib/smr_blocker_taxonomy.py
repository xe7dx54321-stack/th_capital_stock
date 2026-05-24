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
    "VALUATION_STALE",
    "PRICE_STALE",
    "FUNDAMENTALS_STALE_FOR_VALUATION",
    "FORWARD_EPS_MISSING",
    "HISTORICAL_PERCENTILE_MISSING",
    "HISTORICAL_PRICE_HISTORY_MISSING",
    "HISTORICAL_FUNDAMENTALS_MISSING",
    "HISTORICAL_SAMPLE_INSUFFICIENT",
    "HISTORICAL_METRIC_NOT_MEANINGFUL",
    "HISTORICAL_PERCENTILE_PARTIAL",
    "PEER_SET_MISSING",
    "PEER_SET_CONFIG_MISSING",
    "PEER_DATA_MISSING",
    "PEER_PRICE_MISSING",
    "PEER_FUNDAMENTALS_MISSING",
    "PEER_COUNT_INSUFFICIENT",
    "VALUATION_EVIDENCE_MISSING",
    "VALUATION_CONFIDENCE_LOW",
    "HIGH_BEAR_CASE",
    "HIGH_BEAR_CASE_UNRESOLVED",
    "HIGH_BEAR_CASE_PARTIALLY_MITIGATED",
    "DATA_QUALITY_RISK",
    "EVIDENCE_QUALITY_LOW",
    "FILING_CHUNK_RELEVANCE_LOW",
    "FUNDAMENTALS_FIELD_CONFIDENCE_LOW",
    "PROXY_SOURCE_NOT_INDEPENDENT",
    "MISSING_SOURCE_EVIDENCE_ID",
    "AMBIGUOUS_UNIT",
    "TABLE_EXTRACTION_CONFIDENCE_LOW",
    "FIELD_MAPPING_MISSING",
    "FIELD_NOT_FOUND",
    "TABLE_NOT_FOUND",
    "PARSE_FAILED",
    "STALE_SOURCE_EVIDENCE",
    "LOW_DIRECTNESS_EVIDENCE",
    "LOW_TICKER_RELEVANCE",
    "LOW_THEME_RELEVANCE",
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
    "fresh_price": "PRICE_STALE",
    "price_stale": "PRICE_STALE",
    "valuation_stale": "VALUATION_STALE",
    "fundamentals_stale_for_valuation": "FUNDAMENTALS_STALE_FOR_VALUATION",
    "forward_eps": "FORWARD_EPS_MISSING",
    "forward_eps_missing": "FORWARD_EPS_MISSING",
    "historical_percentile": "HISTORICAL_PERCENTILE_MISSING",
    "historical_percentile_missing": "HISTORICAL_PERCENTILE_MISSING",
    "historical_price_history_missing": "HISTORICAL_PRICE_HISTORY_MISSING",
    "historical_fundamentals_missing": "HISTORICAL_FUNDAMENTALS_MISSING",
    "historical_sample_insufficient": "HISTORICAL_SAMPLE_INSUFFICIENT",
    "historical_metric_not_meaningful": "HISTORICAL_METRIC_NOT_MEANINGFUL",
    "historical_percentile_partial": "HISTORICAL_PERCENTILE_PARTIAL",
    "peer_set": "PEER_SET_MISSING",
    "peer_set_missing": "PEER_SET_MISSING",
    "peer_set_config_missing": "PEER_SET_CONFIG_MISSING",
    "peer_data_missing": "PEER_DATA_MISSING",
    "peer_price_missing": "PEER_PRICE_MISSING",
    "peer_fundamentals_missing": "PEER_FUNDAMENTALS_MISSING",
    "peer_count_insufficient": "PEER_COUNT_INSUFFICIENT",
    "valuation_evidence_missing": "VALUATION_EVIDENCE_MISSING",
    "valuation_confidence_low": "VALUATION_CONFIDENCE_LOW",
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
    "high_bear_case_unresolved": "HIGH_BEAR_CASE_UNRESOLVED",
    "high_bear_case_partially_mitigated": "HIGH_BEAR_CASE_PARTIALLY_MITIGATED",
    "bear_case_unresolved": "HIGH_BEAR_CASE_UNRESOLVED",
    "bear_case_partially_mitigated": "HIGH_BEAR_CASE_PARTIALLY_MITIGATED",
    "filing_chunk_relevance_low": "FILING_CHUNK_RELEVANCE_LOW",
    "fundamentals_field_confidence_low": "FUNDAMENTALS_FIELD_CONFIDENCE_LOW",
    "proxy_source_not_independent": "PROXY_SOURCE_NOT_INDEPENDENT",
    "missing_source_evidence_id": "MISSING_SOURCE_EVIDENCE_ID",
    "ambiguous_unit": "AMBIGUOUS_UNIT",
    "table_extraction_confidence_low": "TABLE_EXTRACTION_CONFIDENCE_LOW",
    "mapping_missing": "FIELD_MAPPING_MISSING",
    "field_mapping_missing": "FIELD_MAPPING_MISSING",
    "field_not_found": "FIELD_NOT_FOUND",
    "table_not_found": "TABLE_NOT_FOUND",
    "parse_failed": "PARSE_FAILED",
    "stale_source_evidence": "STALE_SOURCE_EVIDENCE",
    "stale_filing": "STALE_SOURCE_EVIDENCE",
    "low_directness_evidence": "LOW_DIRECTNESS_EVIDENCE",
    "low_ticker_relevance": "LOW_TICKER_RELEVANCE",
    "low_theme_relevance": "LOW_THEME_RELEVANCE",
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
    "VALUATION_STALE": "valuation",
    "PRICE_STALE": "valuation",
    "FUNDAMENTALS_STALE_FOR_VALUATION": "valuation",
    "FORWARD_EPS_MISSING": "valuation",
    "HISTORICAL_PERCENTILE_MISSING": "valuation",
    "HISTORICAL_PRICE_HISTORY_MISSING": "valuation",
    "HISTORICAL_FUNDAMENTALS_MISSING": "valuation",
    "HISTORICAL_SAMPLE_INSUFFICIENT": "valuation",
    "HISTORICAL_METRIC_NOT_MEANINGFUL": "valuation",
    "HISTORICAL_PERCENTILE_PARTIAL": "valuation",
    "PEER_SET_MISSING": "valuation",
    "PEER_SET_CONFIG_MISSING": "valuation",
    "PEER_DATA_MISSING": "valuation",
    "PEER_PRICE_MISSING": "valuation",
    "PEER_FUNDAMENTALS_MISSING": "valuation",
    "PEER_COUNT_INSUFFICIENT": "valuation",
    "VALUATION_EVIDENCE_MISSING": "valuation",
    "VALUATION_CONFIDENCE_LOW": "valuation",
    "HIGH_BEAR_CASE": "risk",
    "HIGH_BEAR_CASE_UNRESOLVED": "risk",
    "HIGH_BEAR_CASE_PARTIALLY_MITIGATED": "risk",
    "DATA_QUALITY_RISK": "data_quality",
    "EVIDENCE_QUALITY_LOW": "evidence",
    "FILING_CHUNK_RELEVANCE_LOW": "evidence",
    "FUNDAMENTALS_FIELD_CONFIDENCE_LOW": "fundamentals",
    "PROXY_SOURCE_NOT_INDEPENDENT": "proxy",
    "MISSING_SOURCE_EVIDENCE_ID": "evidence",
    "AMBIGUOUS_UNIT": "fundamentals",
    "TABLE_EXTRACTION_CONFIDENCE_LOW": "fundamentals",
    "FIELD_MAPPING_MISSING": "fundamentals",
    "FIELD_NOT_FOUND": "fundamentals",
    "TABLE_NOT_FOUND": "fundamentals",
    "PARSE_FAILED": "fundamentals",
    "STALE_SOURCE_EVIDENCE": "evidence",
    "LOW_DIRECTNESS_EVIDENCE": "evidence",
    "LOW_TICKER_RELEVANCE": "evidence",
    "LOW_THEME_RELEVANCE": "evidence",
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
    "VALUATION_STALE": "high",
    "PRICE_STALE": "high",
    "FUNDAMENTALS_STALE_FOR_VALUATION": "high",
    "FORWARD_EPS_MISSING": "medium",
    "HISTORICAL_PERCENTILE_MISSING": "medium",
    "HISTORICAL_PRICE_HISTORY_MISSING": "medium",
    "HISTORICAL_FUNDAMENTALS_MISSING": "medium",
    "HISTORICAL_SAMPLE_INSUFFICIENT": "medium",
    "HISTORICAL_METRIC_NOT_MEANINGFUL": "low",
    "HISTORICAL_PERCENTILE_PARTIAL": "low",
    "PEER_SET_MISSING": "medium",
    "PEER_SET_CONFIG_MISSING": "medium",
    "PEER_DATA_MISSING": "medium",
    "PEER_PRICE_MISSING": "medium",
    "PEER_FUNDAMENTALS_MISSING": "medium",
    "PEER_COUNT_INSUFFICIENT": "medium",
    "VALUATION_EVIDENCE_MISSING": "high",
    "VALUATION_CONFIDENCE_LOW": "medium",
    "HIGH_BEAR_CASE": "high",
    "HIGH_BEAR_CASE_UNRESOLVED": "high",
    "HIGH_BEAR_CASE_PARTIALLY_MITIGATED": "medium",
    "DATA_QUALITY_RISK": "high",
    "EVIDENCE_QUALITY_LOW": "high",
    "FILING_CHUNK_RELEVANCE_LOW": "high",
    "FUNDAMENTALS_FIELD_CONFIDENCE_LOW": "medium",
    "PROXY_SOURCE_NOT_INDEPENDENT": "medium",
    "MISSING_SOURCE_EVIDENCE_ID": "high",
    "AMBIGUOUS_UNIT": "medium",
    "TABLE_EXTRACTION_CONFIDENCE_LOW": "medium",
    "FIELD_MAPPING_MISSING": "medium",
    "FIELD_NOT_FOUND": "medium",
    "TABLE_NOT_FOUND": "high",
    "PARSE_FAILED": "medium",
    "STALE_SOURCE_EVIDENCE": "high",
    "LOW_DIRECTNESS_EVIDENCE": "medium",
    "LOW_TICKER_RELEVANCE": "medium",
    "LOW_THEME_RELEVANCE": "low",
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
    "VALUATION_STALE": "high",
    "PRICE_STALE": "high",
    "FUNDAMENTALS_STALE_FOR_VALUATION": "medium",
    "FORWARD_EPS_MISSING": "medium",
    "HISTORICAL_PERCENTILE_MISSING": "medium",
    "HISTORICAL_PRICE_HISTORY_MISSING": "medium",
    "HISTORICAL_FUNDAMENTALS_MISSING": "medium",
    "HISTORICAL_SAMPLE_INSUFFICIENT": "medium",
    "HISTORICAL_METRIC_NOT_MEANINGFUL": "low",
    "HISTORICAL_PERCENTILE_PARTIAL": "medium",
    "PEER_SET_MISSING": "medium",
    "PEER_SET_CONFIG_MISSING": "high",
    "PEER_DATA_MISSING": "medium",
    "PEER_PRICE_MISSING": "medium",
    "PEER_FUNDAMENTALS_MISSING": "medium",
    "PEER_COUNT_INSUFFICIENT": "medium",
    "VALUATION_EVIDENCE_MISSING": "medium",
    "VALUATION_CONFIDENCE_LOW": "medium",
    "HIGH_BEAR_CASE": "low",
    "HIGH_BEAR_CASE_UNRESOLVED": "low",
    "HIGH_BEAR_CASE_PARTIALLY_MITIGATED": "medium",
    "DATA_QUALITY_RISK": "medium",
    "EVIDENCE_QUALITY_LOW": "medium",
    "FILING_CHUNK_RELEVANCE_LOW": "medium",
    "FUNDAMENTALS_FIELD_CONFIDENCE_LOW": "medium",
    "PROXY_SOURCE_NOT_INDEPENDENT": "medium",
    "MISSING_SOURCE_EVIDENCE_ID": "medium",
    "AMBIGUOUS_UNIT": "medium",
    "TABLE_EXTRACTION_CONFIDENCE_LOW": "medium",
    "FIELD_MAPPING_MISSING": "medium",
    "FIELD_NOT_FOUND": "medium",
    "TABLE_NOT_FOUND": "medium",
    "PARSE_FAILED": "medium",
    "STALE_SOURCE_EVIDENCE": "medium",
    "LOW_DIRECTNESS_EVIDENCE": "medium",
    "LOW_TICKER_RELEVANCE": "medium",
    "LOW_THEME_RELEVANCE": "medium",
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
    "VALUATION_STALE": "recompute valuation snapshot from fresh price and fundamentals",
    "PRICE_STALE": "refresh daily price before valuation can support action",
    "FUNDAMENTALS_STALE_FOR_VALUATION": "refresh fundamentals before recomputing valuation",
    "FORWARD_EPS_MISSING": "extract forward EPS proxy or keep valuation below promotion eligible",
    "HISTORICAL_PERCENTILE_MISSING": "compute or seed historical valuation percentile before using valuation as promotion evidence",
    "HISTORICAL_PRICE_HISTORY_MISSING": "backfill historical prices before computing valuation percentiles",
    "HISTORICAL_FUNDAMENTALS_MISSING": "backfill historical valuation factors before computing percentiles",
    "HISTORICAL_SAMPLE_INSUFFICIENT": "collect a longer valuation history before using percentile as evidence",
    "HISTORICAL_METRIC_NOT_MEANINGFUL": "use a different valuation metric when earnings or denominator is not meaningful",
    "HISTORICAL_PERCENTILE_PARTIAL": "treat partial historical valuation as supporting evidence only",
    "PEER_SET_MISSING": "define an auditable peer set before using relative valuation as promotion evidence",
    "PEER_SET_CONFIG_MISSING": "define a peer-set config for the ticker before relative valuation",
    "PEER_DATA_MISSING": "load price/fundamentals data for configured peers",
    "PEER_PRICE_MISSING": "load latest prices for configured peers",
    "PEER_FUNDAMENTALS_MISSING": "load fundamentals or factor multiples for configured peers",
    "PEER_COUNT_INSUFFICIENT": "add enough peers with usable data before using relative valuation strongly",
    "VALUATION_EVIDENCE_MISSING": "attach price, fundamentals, and valuation source evidence",
    "VALUATION_CONFIDENCE_LOW": "add valuation inputs until confidence reaches supporting-evidence quality",
    "HIGH_BEAR_CASE": "address deal-breaker risk or keep the item below pending review",
    "HIGH_BEAR_CASE_UNRESOLVED": "respond to high bear-case claims with live evidence or keep candidate below pending review",
    "HIGH_BEAR_CASE_PARTIALLY_MITIGATED": "keep candidate reduced-size or below pending review until bear case is fully mitigated",
    "DATA_QUALITY_RISK": "repair freshness or source-quality issues before promotion",
    "EVIDENCE_QUALITY_LOW": "replace low-relevance evidence with high-quality live evidence",
    "FILING_CHUNK_RELEVANCE_LOW": "exclude administrative filing chunks and select investment-relevant sections",
    "FUNDAMENTALS_FIELD_CONFIDENCE_LOW": "improve field extraction confidence or mark field for manual review",
    "PROXY_SOURCE_NOT_INDEPENDENT": "add independent proxy evidence sources",
    "MISSING_SOURCE_EVIDENCE_ID": "link extracted field or claim to a concrete evidence_id",
    "AMBIGUOUS_UNIT": "resolve unit/currency ambiguity before using the extracted field",
    "TABLE_EXTRACTION_CONFIDENCE_LOW": "improve table parsing or move the field to manual review",
    "FIELD_MAPPING_MISSING": "add financial-field synonyms for the missing A/H field",
    "FIELD_NOT_FOUND": "inspect the filing table and add extraction coverage for the missing field",
    "TABLE_NOT_FOUND": "improve financial table detection for the filing source",
    "PARSE_FAILED": "fix parser handling for the matched field/table text",
    "STALE_SOURCE_EVIDENCE": "refresh the source evidence before using it for promotion",
    "LOW_DIRECTNESS_EVIDENCE": "replace indirect evidence with a more direct filing/news excerpt",
    "LOW_TICKER_RELEVANCE": "replace evidence that does not clearly map to the ticker",
    "LOW_THEME_RELEVANCE": "replace evidence that does not support the thesis theme",
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
    "VALUATION_STALE": "may_restore_valuation_gate",
    "PRICE_STALE": "may_restore_valuation_gate",
    "FUNDAMENTALS_STALE_FOR_VALUATION": "may_restore_valuation_gate",
    "FORWARD_EPS_MISSING": "may_keep_valuation_supporting_only",
    "HISTORICAL_PERCENTILE_MISSING": "may_keep_valuation_supporting_only",
    "HISTORICAL_PRICE_HISTORY_MISSING": "may_keep_valuation_supporting_only",
    "HISTORICAL_FUNDAMENTALS_MISSING": "may_keep_valuation_supporting_only",
    "HISTORICAL_SAMPLE_INSUFFICIENT": "may_keep_valuation_supporting_only",
    "HISTORICAL_METRIC_NOT_MEANINGFUL": "may_keep_valuation_supporting_only",
    "HISTORICAL_PERCENTILE_PARTIAL": "may_keep_valuation_supporting_only",
    "PEER_SET_MISSING": "may_keep_valuation_supporting_only",
    "PEER_SET_CONFIG_MISSING": "may_restore_relative_valuation_context",
    "PEER_DATA_MISSING": "may_restore_relative_valuation_context",
    "PEER_PRICE_MISSING": "may_restore_relative_valuation_context",
    "PEER_FUNDAMENTALS_MISSING": "may_restore_relative_valuation_context",
    "PEER_COUNT_INSUFFICIENT": "may_keep_valuation_supporting_only",
    "VALUATION_EVIDENCE_MISSING": "may_restore_valuation_gate",
    "VALUATION_CONFIDENCE_LOW": "may_restore_valuation_gate",
    "HIGH_BEAR_CASE": "may_keep_candidate_shadow_until_risk_is_answered",
    "HIGH_BEAR_CASE_UNRESOLVED": "blocks_pending_review_until_risk_is_answered",
    "HIGH_BEAR_CASE_PARTIALLY_MITIGATED": "may_allow_reduced_candidate_shadow_but_not_pending_review",
    "DATA_QUALITY_RISK": "may_restore_data_quality_gate",
    "EVIDENCE_QUALITY_LOW": "may_restore_core_claim_support",
    "FILING_CHUNK_RELEVANCE_LOW": "may_restore_core_claim_support",
    "FUNDAMENTALS_FIELD_CONFIDENCE_LOW": "may_restore_fundamentals_gate",
    "PROXY_SOURCE_NOT_INDEPENDENT": "may_upgrade_proxy_to_promotion_grade",
    "MISSING_SOURCE_EVIDENCE_ID": "may_restore_evidence_traceability",
    "AMBIGUOUS_UNIT": "may_restore_fundamentals_gate",
    "TABLE_EXTRACTION_CONFIDENCE_LOW": "may_restore_fundamentals_gate",
    "FIELD_MAPPING_MISSING": "may_restore_fundamentals_gate",
    "FIELD_NOT_FOUND": "may_restore_fundamentals_gate",
    "TABLE_NOT_FOUND": "may_restore_fundamentals_gate",
    "PARSE_FAILED": "may_restore_fundamentals_gate",
    "STALE_SOURCE_EVIDENCE": "may_restore_evidence_freshness",
    "LOW_DIRECTNESS_EVIDENCE": "may_restore_core_claim_support",
    "LOW_TICKER_RELEVANCE": "may_restore_core_claim_support",
    "LOW_THEME_RELEVANCE": "may_restore_core_claim_support",
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
