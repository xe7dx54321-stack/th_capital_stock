#!/usr/bin/env python3
"""Deterministic Phase 27 semantic evidence gate."""

from __future__ import annotations

from typing import Any

from smr_semantic_evidence_schema import validate_semantic_extraction


def gate_semantic_extraction(extraction: dict[str, Any], *, source_url: str | None = None, chunk_text: str | None = None) -> dict[str, Any]:
    issues = validate_semantic_extraction(extraction, chunk_text=chunk_text)
    errors = [issue for issue in issues if issue.get("severity") == "error"]
    reasons = [issue.get("message") for issue in issues]
    strength = extraction.get("evidence_strength")
    variable = extraction.get("variable_type")
    status = "partial"
    usage = "scenario_analysis_only"
    confidence = extraction.get("confidence") or "unknown"
    usable_gap = True
    usable_valuation = False
    if errors or not extraction.get("quoted_span"):
        status = "blocked"
        usage = "blocked"
        confidence = "unknown"
        usable_gap = False
        reasons.append("invalid extraction")
    elif variable == "unknown":
        status = "blocked"
        usage = "blocked"
        confidence = "unknown"
        usable_gap = False
        reasons.append("unknown variable")
    elif strength == "industry_forecast":
        status = "proxy_supported" if source_url else "context_only"
        usage = "valuation_support" if source_url else "context_only"
        usable_valuation = bool(source_url)
        reasons.append("industry forecast is not company order")
    elif strength == "management_commentary":
        status = "partial"
        usage = "scenario_analysis_only"
        confidence = "low_to_medium" if confidence == "medium" else confidence
        reasons.append("management_commentary")
    elif strength in {"context_only", "weak", "unusable"}:
        status = "context_only" if strength != "unusable" else "blocked"
        usage = "context_only" if status != "blocked" else "blocked"
        confidence = "low" if status != "blocked" else "unknown"
    elif strength in {"direct_disclosure", "quantified_disclosure"} and extraction.get("is_quantified") and source_url:
        status = "proxy_supported"
        usage = "research_evidence"
        confidence = "medium"
    if not source_url and status not in {"blocked", "context_only"}:
        status = "context_only"
        usage = "context_only"
        confidence = "low"
        reasons.append("no source_url")
    if variable == "customer_allocation_signal" and not extraction.get("customer_names"):
        status = "context_only"
        usage = "context_only"
        confidence = "low"
        reasons.append("no explicit customer name or allocation")
    if variable == "ASP_price_signal" and not extraction.get("is_quantified") and "no_explicit_ASP" in (extraction.get("risk_flags") or []):
        status = "context_only"
        usage = "context_only"
        confidence = "low"
        reasons.append("no explicit ASP or price direction")
    if variable == "order_visibility_signal":
        reasons.append("order visibility is not confirmed order without explicit contract/order language")
    return {
        "source_id": extraction.get("source_id"),
        "chunk_id": extraction.get("chunk_id"),
        "variable_type": variable,
        "evidence_status": status,
        "allowed_usage": usage,
        "usable_for_expectation_gap": usable_gap and status not in {"blocked"},
        "usable_for_valuation_support": usable_valuation,
        "usable_for_promotion": False,
        "confidence_after_gate": confidence,
        "downgrade_reasons": list(dict.fromkeys(str(reason) for reason in reasons if reason)),
        "extraction": extraction,
    }


def gate_semantic_extractions(extractions: list[dict[str, Any]], *, chunks_by_id: dict[str, dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    results = []
    chunks_by_id = chunks_by_id or {}
    for item in extractions:
        chunk = chunks_by_id.get(f"{item.get('source_id')}:{item.get('chunk_id')}") or chunks_by_id.get(str(item.get("chunk_id"))) or {}
        source_url = (chunk.get("metadata") or {}).get("source_url")
        results.append(gate_semantic_extraction(item, source_url=source_url, chunk_text=chunk.get("text")))
    return results
