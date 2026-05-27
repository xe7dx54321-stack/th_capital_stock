#!/usr/bin/env python3
"""Shared Phase 27 semantic evidence pipeline."""

from __future__ import annotations

import sqlite3
from typing import Any

from smr_ir_semantic_extractor import extract_semantic_evidence
from smr_ir_source_inventory import build_ir_source_inventory
from smr_phase25_utils import resolve_phase25_tickers
from smr_real_ir_document_loader import attach_real_text_to_sources
from smr_semantic_candidate_retriever import retrieve_candidate_chunks
from smr_semantic_document_chunker import chunk_sources
from smr_semantic_evidence_gate import gate_semantic_extractions


def build_semantic_pipeline_for_ticker(
    ticker: str,
    *,
    mode: str = "mock",
    conn: sqlite3.Connection | None = None,
    use_real_sources: bool = False,
    allow_mock_fallback: bool = True,
    use_text_cache: bool = False,
    extract_text_if_missing: bool = False,
    skip_metadata_only: bool = True,
) -> dict[str, Any]:
    inventory = build_ir_source_inventory(
        ticker,
        conn=conn,
        use_real_sources=use_real_sources,
        allow_mock_fallback=allow_mock_fallback,
    )
    sources = (inventory.get("source_inventory") or {}).get("sources") or []
    if use_real_sources:
        sources = attach_real_text_to_sources(
            sources,
            use_text_cache=use_text_cache,
            extract_text_if_missing=extract_text_if_missing,
            skip_metadata_only=skip_metadata_only,
        )
    chunks = chunk_sources(sources)
    retrieval = retrieve_candidate_chunks(chunks)
    candidates = retrieval.get("candidate_chunks") or []
    extraction_payload = extract_semantic_evidence(candidates, mode=mode)
    chunks_by_id = {f"{chunk.get('source_id')}:{chunk.get('chunk_id')}": chunk for chunk in chunks}
    gate_results = gate_semantic_extractions(extraction_payload.get("semantic_extractions") or [], chunks_by_id=chunks_by_id)
    return {
        "ticker": ticker,
        "inventory": inventory,
        "chunks": chunks,
        "retrieval": retrieval,
        "semantic_extractions": extraction_payload.get("semantic_extractions") or [],
        "no_extraction_chunks": extraction_payload.get("no_extraction_chunks") or [],
        "gate_results": gate_results,
        "prompt_guardrails": extraction_payload.get("prompt_guardrails"),
        "llm_enabled": bool(extraction_payload.get("llm_enabled")),
        "real_sources_used": sum(1 for source in sources if source.get("real_source")),
        "mock_sources_used": sum(1 for source in sources if source.get("mock_source")),
        "text_unavailable_sources": sum(1 for source in sources if source.get("text_unavailable")),
        "text_cache_hits": sum(1 for source in sources if source.get("text_source") == "text_cache"),
        "document_text_extractions": sum(1 for source in sources if source.get("text_source") == "document_text_extraction"),
        "metadata_only_skipped": sum(1 for source in sources if source.get("extraction_status") == "metadata_only"),
        "quoted_span_validated": sum(1 for item in extraction_payload.get("semantic_extractions") or [] if item.get("quoted_span")),
        "source_url_preserved": sum(
            1
            for gate in gate_results
            if (chunks_by_id.get(f"{gate.get('source_id')}:{gate.get('chunk_id')}") or {}).get("metadata", {}).get("source_url")
        ),
    }


def build_semantic_pipeline(
    tickers: str | None = None,
    *,
    mode: str = "mock",
    conn: sqlite3.Connection | None = None,
    use_real_sources: bool = False,
    allow_mock_fallback: bool = True,
    use_text_cache: bool = False,
    extract_text_if_missing: bool = False,
    skip_metadata_only: bool = True,
) -> dict[str, Any]:
    resolved = resolve_phase25_tickers(tickers)
    rows = [
        build_semantic_pipeline_for_ticker(
            ticker,
            mode=mode,
            conn=conn,
            use_real_sources=use_real_sources,
            allow_mock_fallback=allow_mock_fallback,
            use_text_cache=use_text_cache,
            extract_text_if_missing=extract_text_if_missing,
            skip_metadata_only=skip_metadata_only,
        )
        for ticker in resolved
    ]
    return {
        "tickers": resolved,
        "rows": rows,
        "summary": {
            "tickers_checked": len(rows),
            "sources_found": sum((row.get("inventory", {}).get("source_inventory") or {}).get("sources_found", 0) for row in rows),
            "candidate_chunks": sum(len((row.get("retrieval") or {}).get("candidate_chunks") or []) for row in rows),
            "semantic_extractions": sum(len(row.get("semantic_extractions") or []) for row in rows),
            "passed_gate": sum(1 for row in rows for gate in row.get("gate_results") or [] if gate.get("evidence_status") not in {"blocked"}),
            "blocked_or_downgraded": sum(1 for row in rows for gate in row.get("gate_results") or [] if gate.get("evidence_status") in {"blocked", "context_only"}),
            "llm_enabled": any(row.get("llm_enabled") for row in rows),
            "real_sources_used": sum(row.get("real_sources_used") or 0 for row in rows),
            "mock_sources_used": sum(row.get("mock_sources_used") or 0 for row in rows),
            "chunks_processed": sum(len(row.get("chunks") or []) for row in rows),
            "chunks_created": sum(len(row.get("chunks") or []) for row in rows),
            "text_unavailable_sources": sum(row.get("text_unavailable_sources") or 0 for row in rows),
            "text_cache_hits": sum(row.get("text_cache_hits") or 0 for row in rows),
            "document_text_extractions": sum(row.get("document_text_extractions") or 0 for row in rows),
            "metadata_only_skipped": sum(row.get("metadata_only_skipped") or 0 for row in rows),
            "quoted_span_validated": sum(row.get("quoted_span_validated") or 0 for row in rows),
            "source_url_preserved": sum(row.get("source_url_preserved") or 0 for row in rows),
        },
    }
