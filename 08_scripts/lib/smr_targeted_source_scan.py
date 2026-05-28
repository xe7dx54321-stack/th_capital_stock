#!/usr/bin/env python3
"""Phase 37 targeted source scan over existing local evidence state."""

from __future__ import annotations

import sqlite3
from typing import Any

from smr_controlled_acquisition_selector import build_controlled_acquisition_selection
from smr_evidence_lifecycle import list_semantic_evidence_candidates
from smr_post_governance_evidence_state import normalize_research_variable
from smr_real_ir_source_connector import discover_real_ir_sources
from smr_text_cache import read_text_cache
from smr_wiki import now_ts


VARIABLE_ALIASES = {
    "ASP_price_proxy": {"ASP_price_proxy", "ASP_price_signal", "margin_signal"},
    "shipment": {"shipment", "shipment_signal"},
    "order_visibility": {"order_visibility", "order_visibility_signal"},
    "customer_allocation_proxy": {"customer_allocation_proxy", "customer_allocation_signal"},
    "industry_forecast": {"industry_forecast", "end_demand_signal"},
    "official_consensus": {"official_consensus", "consensus_expectation_proxy", "internal_consensus_proxy"},
}

KEYWORDS = {
    "ASP_price_proxy": ["ASP", "price", "pricing", "product mix", "毛利", "价格", "产品结构", "800G", "1.6T"],
    "shipment": ["shipment", "delivery", "出货", "交付", "多出货"],
    "order_visibility": ["order", "backlog", "订单", "需求", "能见度", "在手订单"],
    "customer_allocation_proxy": ["customer", "客户", "北美", "云厂商", "allocation"],
    "industry_forecast": ["forecast", "industry", "市场", "需求", "800G", "1.6T"],
    "official_consensus": ["consensus", "一致预期", "预期"],
}


def _matches_variable(candidate: dict[str, Any], variable: str) -> bool:
    raw = str(candidate.get("variable_type") or "")
    normalized = normalize_research_variable(raw)
    aliases = VARIABLE_ALIASES.get(variable, {variable})
    if raw in aliases or normalized in aliases:
        return True
    text = f"{candidate.get('quoted_span') or ''} {candidate.get('claim_text') or ''}".lower()
    return any(keyword.lower() in text for keyword in KEYWORDS.get(variable, []))


def _chunk_from_candidate(task: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any] | None:
    quoted = str(candidate.get("quoted_span") or "").strip()
    source_url = candidate.get("source_url")
    if not quoted or not source_url:
        return None
    return {
        "task_id": task.get("task_id"),
        "variable": task.get("variable"),
        "task_type": task.get("task_type"),
        "source_id": candidate.get("source_id"),
        "source_url": source_url,
        "source_type": candidate.get("source_type"),
        "source_origin": "existing_semantic_evidence",
        "original_evidence_id": candidate.get("evidence_id"),
        "chunk_id": f"phase37_chunk_{candidate.get('evidence_id')}",
        "chunk_text": " ".join([quoted, str(candidate.get("claim_text") or "")]).strip(),
        "quoted_span": quoted,
        "allowed_usage_target": task.get("allowed_usage_target"),
        "limitations": candidate.get("limitations") or [],
    }


def _chunks_from_text_cache(task: dict[str, Any], source: dict[str, Any]) -> list[dict[str, Any]]:
    text = read_text_cache(str(source.get("source_id") or ""), source.get("source_url")) or source.get("text_snippet") or ""
    if not text:
        return []
    variable = str(task.get("variable") or "")
    keywords = KEYWORDS.get(variable, [])
    lines = [line.strip() for line in str(text).replace("。", "。\n").splitlines() if line.strip()]
    chunks = []
    for index, line in enumerate(lines[:80]):
        if len(chunks) >= 2:
            break
        if any(keyword.lower() in line.lower() for keyword in keywords):
            chunks.append(
                {
                    "task_id": task.get("task_id"),
                    "variable": variable,
                    "task_type": task.get("task_type"),
                    "source_id": source.get("source_id"),
                    "source_url": source.get("source_url"),
                    "source_type": source.get("source_type"),
                    "source_origin": "text_cache_or_snippet",
                    "original_evidence_id": None,
                    "chunk_id": f"phase37_text_{source.get('source_id')}_{index}",
                    "chunk_text": line,
                    "quoted_span": line[:280],
                    "allowed_usage_target": task.get("allowed_usage_target"),
                    "limitations": ["text cache/snippet scan; requires candidate guard before persistence"],
                }
            )
    return chunks


def build_targeted_source_scan(
    conn: sqlite3.Connection,
    ticker: str,
    *,
    limit: int | None = None,
    task_id: str | None = None,
    dry_run: bool = True,
) -> dict[str, Any]:
    ticker = str(ticker or "").strip().upper()
    selection = build_controlled_acquisition_selection(conn, ticker, limit=limit)
    selected = (selection.get("controlled_acquisition_selection") or {}).get("selected_tasks") or []
    if task_id:
        selected = [task for task in selected if task.get("task_id") == task_id]
    semantic_candidates = list_semantic_evidence_candidates(conn, ticker=ticker)
    real_sources = discover_real_ir_sources(conn, ticker, limit=12)
    text_cache_hits = sum(1 for source in real_sources if read_text_cache(str(source.get("source_id") or ""), source.get("source_url")))
    scan_results = []
    all_chunks: list[dict[str, Any]] = []
    for task in selected:
        variable = str(task.get("variable") or "")
        chunks = [
            chunk
            for candidate in semantic_candidates
            if _matches_variable(candidate, variable)
            for chunk in [_chunk_from_candidate(task, candidate)]
            if chunk
        ]
        if not chunks:
            for source in real_sources:
                chunks.extend(_chunks_from_text_cache(task, source))
        chunks = chunks[:3]
        all_chunks.extend(chunks)
        scan_results.append(
            {
                "task_id": task.get("task_id"),
                "variable": variable,
                "candidate_chunks_found": len(chunks),
                "best_source_type": (chunks[0] if chunks else {}).get("source_type"),
                "best_source_url": (chunks[0] if chunks else {}).get("source_url"),
                "scan_status": "candidate_chunks_found" if chunks else "text_unavailable_or_no_matching_existing_source",
                "candidate_chunks": chunks,
            }
        )
    sources_scanned = {
        str(item.get("source_id") or item.get("source_url"))
        for item in list(real_sources) + semantic_candidates
        if item.get("source_id") or item.get("source_url")
    }
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "mode": "dry_run" if dry_run else "scan_only",
        "targeted_source_scan": {
            "tasks_checked": len(selected),
            "sources_scanned": len(sources_scanned),
            "text_cache_hits": text_cache_hits,
            "candidate_chunks_found": len(all_chunks),
            "source_missing": sum(1 for row in scan_results if row.get("candidate_chunks_found") == 0),
            "scan_results": scan_results,
        },
        "safety": {
            "scan_only": True,
            "dry_run_wrote_db": False,
            "raw_content_saved": False,
            "external_fetch_executed": False,
            "metadata_fabricated_as_body": False,
            "new_pending_created": 0,
        },
    }
