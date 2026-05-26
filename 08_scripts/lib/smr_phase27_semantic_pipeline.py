#!/usr/bin/env python3
"""Shared Phase 27 semantic evidence pipeline."""

from __future__ import annotations

from typing import Any

from smr_ir_semantic_extractor import extract_semantic_evidence
from smr_ir_source_inventory import build_ir_source_inventory
from smr_phase25_utils import resolve_phase25_tickers
from smr_semantic_candidate_retriever import retrieve_candidate_chunks
from smr_semantic_document_chunker import chunk_sources
from smr_semantic_evidence_gate import gate_semantic_extractions


def build_semantic_pipeline_for_ticker(ticker: str, *, mode: str = "mock") -> dict[str, Any]:
    inventory = build_ir_source_inventory(ticker)
    sources = (inventory.get("source_inventory") or {}).get("sources") or []
    chunks = chunk_sources(sources)
    retrieval = retrieve_candidate_chunks(chunks)
    candidates = retrieval.get("candidate_chunks") or []
    extraction_payload = extract_semantic_evidence(candidates, mode=mode)
    chunks_by_id = {chunk.get("chunk_id"): chunk for chunk in chunks}
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
    }


def build_semantic_pipeline(tickers: str | None = None, *, mode: str = "mock") -> dict[str, Any]:
    resolved = resolve_phase25_tickers(tickers)
    rows = [build_semantic_pipeline_for_ticker(ticker, mode=mode) for ticker in resolved]
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
        },
    }
