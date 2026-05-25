#!/usr/bin/env python3
"""Conservative thesis inference helpers for Phase 14.

The inference result is intentionally advisory: low confidence or unknown
thesis must keep the candidate out of automatic pending review.
"""

from __future__ import annotations

import json
import re
from typing import Any


SUPPORTED_THESIS_TYPES = {
    "valuation_rerating",
    "earnings_revision",
    "revenue_growth",
    "margin_improvement",
    "cash_flow_improvement",
    "shareholder_return",
    "cloud_growth",
    "ai_infrastructure_demand",
    "cost_reduction",
    "balance_sheet_repair",
    "event_driven",
    "technical_momentum",
}


def _lower_json(value: Any) -> str:
    try:
        raw = json.dumps(value or {}, ensure_ascii=False, default=str)
    except TypeError:
        raw = str(value or "")
    return raw.lower()


def _claim_text(claims: list[dict[str, Any]] | None) -> str:
    return " ".join(
        " ".join(
            str(claim.get(key) or "")
            for key in ("claim_text", "text", "claim_type", "theme", "stance", "summary")
        )
        for claim in (claims or [])
        if isinstance(claim, dict)
    ).lower()


def _contains(text: str, *tokens: str) -> bool:
    return any(token in text for token in tokens)


def _add_score(
    scores: dict[str, float],
    signals: dict[str, list[str]],
    thesis_type: str,
    amount: float,
    signal: str,
) -> None:
    if thesis_type not in SUPPORTED_THESIS_TYPES:
        return
    scores[thesis_type] = scores.get(thesis_type, 0.0) + amount
    signals.setdefault(thesis_type, [])
    if signal not in signals[thesis_type]:
        signals[thesis_type].append(signal)


def _valuation_status(valuation: dict[str, Any]) -> tuple[str, str, str]:
    peer = valuation.get("peer_comparison") or {}
    historical = valuation.get("historical_valuation") or {}
    return (
        str(valuation.get("allowed_usage") or "").lower(),
        str(peer.get("peer_comparison_status") or valuation.get("peer_comparison_status") or "").lower(),
        str(historical.get("status") or valuation.get("historical_percentile_status") or "").lower(),
    )


def _confidence(top_score: float, second_score: float) -> float:
    if top_score <= 0:
        return 0.0
    separation = max(0.0, top_score - second_score)
    return round(min(0.95, top_score + min(0.12, separation / 3.0)), 2)


def infer_thesis_type(
    ticker: str,
    claims: list[dict[str, Any]] | None = None,
    candidate: dict[str, Any] | None = None,
    proxy: dict[str, Any] | None = None,
    valuation: dict[str, Any] | None = None,
    bear_case: dict[str, Any] | None = None,
    market_signal: dict[str, Any] | None = None,
    watchlist_item: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Infer the current thesis type from structured inputs.

    The rules are deliberately conservative. A result below 0.5 confidence is
    returned as unknown and must not be used for automatic pending promotion.
    """

    ticker = str(ticker or "").upper()
    candidate = candidate or {}
    proxy = proxy or {}
    valuation = valuation or {}
    bear_case = bear_case or {}
    market_signal = market_signal or {}
    watchlist_item = watchlist_item or {}
    text = " ".join(
        [
            ticker.lower(),
            _claim_text(claims),
            _lower_json(candidate),
            _lower_json(proxy),
            _lower_json(bear_case),
            _lower_json(market_signal),
            _lower_json(watchlist_item),
        ]
    )
    theme = str(watchlist_item.get("theme") or candidate.get("theme") or "").lower()
    sector = str(watchlist_item.get("sector") or candidate.get("sector") or "").lower()
    scores: dict[str, float] = {}
    signals: dict[str, list[str]] = {}

    allowed_usage, peer_status, historical_status = _valuation_status(valuation)
    if allowed_usage in {"supporting_evidence", "promotion_eligible"}:
        _add_score(scores, signals, "valuation_rerating", 0.22, "valuation_snapshot_supporting")
    if peer_status in {"supporting", "promotion_supporting"}:
        _add_score(scores, signals, "valuation_rerating", 0.2, "peer_comparison_supporting")
    if historical_status in {"partial", "available"}:
        _add_score(scores, signals, "valuation_rerating", 0.2, "historical_valuation_available")
    if _contains(text, "valuation", "rerating", "re-rating", "discount", "multiple", "peer", "historical percentile"):
        _add_score(scores, signals, "valuation_rerating", 0.22, "valuation_related_text")

    if _contains(text, "cloud", "azure", "aws", "aliyun", "tencent cloud", "cloud revenue") or "cloud" in theme or "cloud" in sector:
        _add_score(scores, signals, "cloud_growth", 0.5, "cloud_growth_signal")
    if _contains(text, "buyback", "dividend", "shareholder return", "capital return"):
        _add_score(scores, signals, "shareholder_return", 0.52, "shareholder_return_signal")
    if _contains(text, "capex", "fcf", "free cash flow", "operating cash flow", "cash flow"):
        _add_score(scores, signals, "cash_flow_improvement", 0.55, "cash_flow_signal")
    if _contains(text, "gross margin", "operating margin", "margin improvement"):
        _add_score(scores, signals, "margin_improvement", 0.5, "margin_signal")
    if _contains(text, "cost reduction", "cost cut", "efficiency", "opex reduction"):
        _add_score(scores, signals, "cost_reduction", 0.5, "cost_reduction_signal")
    if _contains(text, "balance sheet", "deleverag", "debt reduction", "cash balance"):
        _add_score(scores, signals, "balance_sheet_repair", 0.5, "balance_sheet_signal")
    if _contains(text, "event", "spin-off", "spinoff", "catalyst", "regulatory approval"):
        _add_score(scores, signals, "event_driven", 0.45, "event_signal")
    if _contains(text, "momentum", "breakout", "technical", "moving average"):
        _add_score(scores, signals, "technical_momentum", 0.45, "technical_signal")

    proxy_quality = str(proxy.get("proxy_quality") or "").lower()
    if proxy_quality == "strong":
        _add_score(scores, signals, "earnings_revision", 0.24, "strong_proxy_quality")
    elif proxy_quality == "medium":
        _add_score(scores, signals, "earnings_revision", 0.12, "medium_proxy_quality")
    if _contains(text, "eps surprise", "earnings revision", "estimate revision", "guidance raise"):
        _add_score(scores, signals, "earnings_revision", 0.42, "earnings_revision_text")
    if _contains(text, "revenue growth", "sales growth", "top line", "revenue guidance"):
        _add_score(scores, signals, "revenue_growth", 0.45, "revenue_growth_text")

    ai_theme_tokens = (
        "semiconductor_compute",
        "semiconductor_photonics",
        "ai_infrastructure",
        "gpu",
        "accelerator",
        "compute",
    )
    if any(token in theme or token in sector or token in text for token in ai_theme_tokens):
        _add_score(scores, signals, "ai_infrastructure_demand", 0.55, "ai_infrastructure_theme")
    if _contains(text, "ai demand", "gpu demand", "compute demand", "ai server", "accelerator demand"):
        _add_score(scores, signals, "ai_infrastructure_demand", 0.32, "ai_infrastructure_text")

    explicit = str(candidate.get("thesis_type") or market_signal.get("thesis_type") or "").strip()
    if explicit in SUPPORTED_THESIS_TYPES:
        _add_score(scores, signals, explicit, 0.65, "explicit_structured_thesis")
    for item in candidate.get("thesis_types") or []:
        if str(item) in SUPPORTED_THESIS_TYPES:
            _add_score(scores, signals, str(item), 0.45, "explicit_structured_thesis_list")
    for item in watchlist_item.get("candidate_thesis_hints") or []:
        if str(item) in SUPPORTED_THESIS_TYPES:
            _add_score(scores, signals, str(item), 0.34, "watchlist_candidate_thesis_hint")
    if watchlist_item.get("theme_tags"):
        tag_text = _lower_json(watchlist_item.get("theme_tags"))
        if _contains(tag_text, "ai_infrastructure", "compute_hardware", "server_supply_chain"):
            _add_score(scores, signals, "ai_infrastructure_demand", 0.26, "watchlist_theme_tags")
    if watchlist_item.get("business_driver"):
        driver = str(watchlist_item.get("business_driver") or "").lower()
        if _contains(driver, "ai server", "compute infrastructure", "server supply chain"):
            _add_score(scores, signals, "ai_infrastructure_demand", 0.22, "watchlist_business_driver")
    if watchlist_item.get("claim_keywords"):
        keywords = _lower_json(watchlist_item.get("claim_keywords"))
        if _contains(keywords, "ai server", "compute", "infrastructure", "order demand"):
            _add_score(scores, signals, "ai_infrastructure_demand", 0.18, "watchlist_claim_keywords")
        if _contains(keywords, "revenue growth", "sales growth"):
            _add_score(scores, signals, "revenue_growth", 0.16, "watchlist_claim_keywords")
    if watchlist_item.get("proxy_signal_hints"):
        proxy_hints = _lower_json(watchlist_item.get("proxy_signal_hints"))
        if _contains(proxy_hints, "order", "guidance", "industry demand"):
            _add_score(scores, signals, "ai_infrastructure_demand", 0.12, "watchlist_proxy_signal_hints")
        if _contains(proxy_hints, "revenue growth"):
            _add_score(scores, signals, "revenue_growth", 0.12, "watchlist_proxy_signal_hints")

    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    if not ranked:
        return {
            "ticker": ticker,
            "inferred_thesis_types": [],
            "primary_thesis_type": "unknown",
            "confidence": 0.0,
            "signals_used": [],
            "fallback_used": True,
            "needs_manual_thesis_review": True,
            "scorecard": {},
        }

    top_type, top_score = ranked[0]
    second_score = ranked[1][1] if len(ranked) > 1 else 0.0
    confidence = _confidence(top_score, second_score)
    inferred = [name for name, score in ranked if score >= 0.35]
    if confidence < 0.5:
        return {
            "ticker": ticker,
            "inferred_thesis_types": inferred,
            "primary_thesis_type": "unknown",
            "confidence": confidence,
            "signals_used": signals.get(top_type, []),
            "fallback_used": True,
            "needs_manual_thesis_review": True,
            "scorecard": {name: round(score, 3) for name, score in ranked},
        }
    return {
        "ticker": ticker,
        "inferred_thesis_types": inferred,
        "primary_thesis_type": top_type,
        "confidence": confidence,
        "signals_used": signals.get(top_type, []),
        "fallback_used": False,
        "needs_manual_thesis_review": False,
        "scorecard": {name: round(score, 3) for name, score in ranked},
    }


def thesis_inference_allows_auto_pending(inference: dict[str, Any]) -> bool:
    return (
        str(inference.get("primary_thesis_type") or "unknown") != "unknown"
        and float(inference.get("confidence") or 0.0) >= 0.5
        and not bool(inference.get("needs_manual_thesis_review"))
    )


def infer_from_text_blob(ticker: str, text: str) -> dict[str, Any]:
    """Small convenience wrapper used by tests and scripts."""

    return infer_thesis_type(ticker, claims=[{"claim_text": re.sub(r"\s+", " ", text or "")}])
