#!/usr/bin/env python3
"""Phase 37 deterministic targeted semantic extraction."""

from __future__ import annotations

import sqlite3
from typing import Any

from smr_targeted_source_scan import build_targeted_source_scan
from smr_wiki import now_ts


VARIABLE_TO_CLAIM = {
    "ASP_price_proxy": "product_mix_or_price_trend_commentary",
    "margin_signal": "margin_or_product_mix_commentary",
    "shipment": "shipment_or_delivery_commentary",
    "order_visibility": "order_visibility_or_demand_commentary",
    "customer_allocation_proxy": "customer_allocation_proxy_only",
    "industry_forecast": "industry_context_forecast",
    "official_consensus": "official_consensus_source_availability_only",
}


def _limitations(variable: str, chunk: dict[str, Any]) -> list[str]:
    base = list(chunk.get("limitations") or [])
    if variable == "ASP_price_proxy":
        base.extend(["does not disclose exact ASP unless quoted span explicitly says so", "do not treat product mix as ASP"])
    if variable == "customer_allocation_proxy":
        base.extend(["does not confirm customer allocation", "do not infer named customer allocation"])
    if variable == "order_visibility":
        base.append("management commentary is not confirmed order")
    if variable == "industry_forecast":
        base.append("industry forecast is not company-specific order evidence")
    if variable == "official_consensus":
        base.append("source availability is not official consensus data")
    return list(dict.fromkeys(base))


def _allowed_usage(variable: str, chunk: dict[str, Any]) -> str:
    target = str(chunk.get("allowed_usage_target") or "")
    if variable == "customer_allocation_proxy":
        return "scenario_analysis_only"
    if variable == "official_consensus":
        return "context_only"
    if variable == "ASP_price_proxy":
        return "valuation_support" if "valuation" in target else "supporting_evidence"
    if variable in {"shipment", "order_visibility"}:
        return "supporting_evidence"
    if variable == "industry_forecast":
        return "context_or_valuation_support"
    return target or "context_only"


def build_targeted_semantic_extraction(
    conn: sqlite3.Connection,
    ticker: str,
    *,
    limit: int | None = None,
    task_id: str | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    scan = build_targeted_source_scan(conn, ticker, limit=limit, task_id=task_id, dry_run=dry_run)
    scan_results = (scan.get("targeted_source_scan") or {}).get("scan_results") or []
    extractions: list[dict[str, Any]] = []
    invalid = 0
    chunks_checked = 0
    for result in scan_results:
        for chunk in result.get("candidate_chunks") or []:
            chunks_checked += 1
            quoted = str(chunk.get("quoted_span") or "")
            chunk_text = str(chunk.get("chunk_text") or "")
            if not quoted or quoted not in chunk_text:
                invalid += 1
                continue
            variable = str(chunk.get("variable") or result.get("variable") or "")
            extractions.append(
                {
                    "task_id": chunk.get("task_id"),
                    "variable": variable,
                    "claim_type": VARIABLE_TO_CLAIM.get(variable, "targeted_research_commentary"),
                    "quoted_span": quoted,
                    "source_url": chunk.get("source_url"),
                    "source_id": chunk.get("source_id"),
                    "source_type": chunk.get("source_type"),
                    "chunk_id": chunk.get("chunk_id"),
                    "chunk_text": chunk_text,
                    "evidence_strength": "management_commentary" if chunk.get("source_type") != "industry_public_commentary" else "industry_context",
                    "allowed_usage_suggestion": _allowed_usage(variable, chunk),
                    "limitations": _limitations(variable, chunk),
                    "source_origin": chunk.get("source_origin"),
                    "original_evidence_id": chunk.get("original_evidence_id"),
                }
            )
    return {
        "generated_at": now_ts(),
        "ticker": scan.get("ticker"),
        "mode": "dry_run" if dry_run else "extraction_only",
        "targeted_semantic_extraction": {
            "tasks_checked": (scan.get("targeted_source_scan") or {}).get("tasks_checked", 0),
            "candidate_chunks_checked": chunks_checked,
            "semantic_extractions": len(extractions),
            "quoted_span_validated": len(extractions),
            "invalid_extractions": invalid,
            "extractions": extractions,
        },
        "safety": {
            "llm_enabled": False,
            "quoted_span_from_chunk": invalid == 0,
            "product_mix_auto_converted_to_asp": False,
            "customer_demand_converted_to_confirmed_order": False,
            "industry_forecast_as_company_order": False,
            "official_consensus_data_fabricated": False,
            "new_pending_created": 0,
        },
    }
