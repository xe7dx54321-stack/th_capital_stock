#!/usr/bin/env python3
"""Phase 27 semantic evidence extraction schema.

The schema is intentionally conservative: an extraction is only usable when it
has source/chunk provenance and a quoted span that appears in the source chunk.
"""

from __future__ import annotations

from typing import Any

from smr_supplier_exposure_model import normalize_ticker


VARIABLE_TYPES = {
    "product_exposure",
    "capacity_signal",
    "shipment_signal",
    "ASP_price_signal",
    "margin_signal",
    "customer_allocation_signal",
    "order_visibility_signal",
    "end_demand_signal",
    "industry_forecast_signal",
    "expectation_signal",
    "risk_signal",
    "supplier_share_signal",
    "consensus_signal",
    "unknown",
}
EVIDENCE_STRENGTHS = {
    "direct_disclosure",
    "quantified_disclosure",
    "management_commentary",
    "industry_forecast",
    "third_party_commentary",
    "proxy_indication",
    "context_only",
    "weak",
    "unusable",
}
DIRECTIONS = {"positive", "negative", "neutral", "mixed", "unknown"}
CONFIDENCES = {"high", "medium", "low_to_medium", "low", "unknown"}
CONFIDENCE_RANK = {"unknown": 0, "low": 1, "low_to_medium": 2, "medium": 3, "high": 4}
STRENGTH_CONFIDENCE_CAP = {
    "direct_disclosure": "high",
    "quantified_disclosure": "high",
    "management_commentary": "medium",
    "industry_forecast": "medium",
    "third_party_commentary": "low_to_medium",
    "proxy_indication": "low_to_medium",
    "context_only": "low",
    "weak": "low",
    "unusable": "unknown",
}


def confidence_cap(evidence_strength: str, confidence: str) -> str:
    cap = STRENGTH_CONFIDENCE_CAP.get(evidence_strength, "unknown")
    return confidence if CONFIDENCE_RANK.get(confidence, 0) <= CONFIDENCE_RANK.get(cap, 0) else cap


def make_semantic_extraction(
    *,
    ticker: str,
    theme: str,
    source_id: str,
    chunk_id: str,
    source_type: str,
    variable_type: str,
    claim_text: str,
    quoted_span: str,
    direction: str = "unknown",
    evidence_strength: str = "weak",
    confidence: str = "unknown",
    is_company_specific: bool = False,
    is_customer_specific: bool = False,
    is_quantified: bool = False,
    time_horizon: str = "unknown",
    numeric_values: list[Any] | None = None,
    customer_names: list[str] | None = None,
    product_mentions: list[str] | None = None,
    risk_flags: list[str] | None = None,
    limitations: list[str] | None = None,
) -> dict[str, Any]:
    if variable_type not in VARIABLE_TYPES:
        variable_type = "unknown"
    if evidence_strength not in EVIDENCE_STRENGTHS:
        evidence_strength = "unusable"
    if direction not in DIRECTIONS:
        direction = "unknown"
    if confidence not in CONFIDENCES:
        confidence = "unknown"
    confidence = confidence_cap(evidence_strength, confidence)
    return {
        "ticker": normalize_ticker(ticker),
        "theme": theme,
        "source_id": str(source_id or ""),
        "chunk_id": str(chunk_id or ""),
        "source_type": str(source_type or "unknown"),
        "variable_type": variable_type,
        "claim_text": str(claim_text or ""),
        "quoted_span": str(quoted_span or ""),
        "direction": direction,
        "evidence_strength": evidence_strength,
        "confidence": confidence,
        "is_company_specific": bool(is_company_specific),
        "is_customer_specific": bool(is_customer_specific),
        "is_quantified": bool(is_quantified),
        "time_horizon": str(time_horizon or "unknown"),
        "numeric_values": numeric_values or [],
        "customer_names": customer_names or [],
        "product_mentions": product_mentions or [],
        "risk_flags": risk_flags or [],
        "limitations": limitations or [],
    }


def validate_semantic_extraction(item: dict[str, Any], *, chunk_text: str | None = None) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if not item.get("source_id"):
        issues.append({"severity": "error", "path": "source_id", "message": "source_id is required"})
    if not item.get("chunk_id"):
        issues.append({"severity": "error", "path": "chunk_id", "message": "chunk_id is required"})
    quoted = str(item.get("quoted_span") or "")
    if not quoted:
        issues.append({"severity": "error", "path": "quoted_span", "message": "quoted_span is required"})
    if chunk_text is not None and quoted and quoted not in chunk_text:
        issues.append({"severity": "error", "path": "quoted_span", "message": "quoted_span must come from input chunk"})
    if item.get("variable_type") not in VARIABLE_TYPES:
        issues.append({"severity": "error", "path": "variable_type", "message": "invalid variable_type"})
    if item.get("variable_type") == "unknown":
        issues.append({"severity": "warning", "path": "variable_type", "message": "unknown variable cannot enter variable evidence pack"})
    if item.get("evidence_strength") not in EVIDENCE_STRENGTHS:
        issues.append({"severity": "error", "path": "evidence_strength", "message": "invalid evidence_strength"})
    if item.get("direction") not in DIRECTIONS:
        issues.append({"severity": "error", "path": "direction", "message": "invalid direction"})
    if item.get("confidence") not in CONFIDENCES:
        issues.append({"severity": "error", "path": "confidence", "message": "invalid confidence"})
    cap = STRENGTH_CONFIDENCE_CAP.get(str(item.get("evidence_strength")), "unknown")
    if CONFIDENCE_RANK.get(str(item.get("confidence")), 0) > CONFIDENCE_RANK.get(cap, 0):
        issues.append({"severity": "error", "path": "confidence", "message": "confidence exceeds evidence strength cap"})
    for name in item.get("customer_names") or []:
        if chunk_text is not None and name and name not in chunk_text:
            issues.append({"severity": "error", "path": "customer_names", "message": "customer name not present in chunk"})
    for value in item.get("numeric_values") or []:
        if chunk_text is not None and str(value) not in chunk_text:
            issues.append({"severity": "error", "path": "numeric_values", "message": "numeric value not present in chunk"})
    return issues


def is_valid_semantic_extraction(item: dict[str, Any], *, chunk_text: str | None = None) -> bool:
    return not any(issue.get("severity") == "error" for issue in validate_semantic_extraction(item, chunk_text=chunk_text))
