#!/usr/bin/env python3
"""Persist Phase 28 semantic evidence candidates."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from typing import Any

from smr_phase25_utils import resolve_phase25_tickers
from smr_phase27_semantic_pipeline import build_semantic_pipeline, build_semantic_pipeline_for_ticker
from smr_wiki import now_ts


def ensure_semantic_evidence_candidate_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS semantic_evidence_candidates (
            evidence_id TEXT PRIMARY KEY,
            ticker TEXT NOT NULL,
            theme TEXT,
            source_id TEXT NOT NULL,
            source_url TEXT NOT NULL,
            source_type TEXT,
            chunk_id TEXT NOT NULL,
            quoted_span TEXT NOT NULL,
            variable_type TEXT,
            claim_text TEXT,
            evidence_status TEXT,
            allowed_usage TEXT,
            usable_for_expectation_gap INTEGER NOT NULL DEFAULT 0,
            usable_for_valuation_support INTEGER NOT NULL DEFAULT 0,
            usable_for_promotion INTEGER NOT NULL DEFAULT 0,
            limitations_json TEXT NOT NULL DEFAULT '[]',
            payload_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_semantic_evidence_candidate_dedupe
        ON semantic_evidence_candidates(source_id, chunk_id, quoted_span)
        """
    )


def semantic_candidate_id(source_id: str, chunk_id: str, quoted_span: str) -> str:
    digest = hashlib.sha1(f"{source_id}|{chunk_id}|{quoted_span}".encode("utf-8")).hexdigest()[:16]
    return f"ev_semantic_ir_{digest}"


def gate_result_to_candidate(gate: dict[str, Any], *, chunk: dict[str, Any] | None = None) -> dict[str, Any] | None:
    extraction = gate.get("extraction") or {}
    chunk = chunk or {}
    metadata = chunk.get("metadata") or {}
    source_url = metadata.get("source_url")
    quoted_span = extraction.get("quoted_span")
    if gate.get("evidence_status") == "blocked" or not source_url or not quoted_span or metadata.get("mock_source"):
        return None
    return {
        "evidence_id": semantic_candidate_id(str(gate.get("source_id")), str(gate.get("chunk_id")), str(quoted_span)),
        "ticker": extraction.get("ticker"),
        "theme": extraction.get("theme"),
        "source_id": gate.get("source_id"),
        "source_url": source_url,
        "source_type": extraction.get("source_type"),
        "chunk_id": gate.get("chunk_id"),
        "quoted_span": quoted_span,
        "variable_type": gate.get("variable_type"),
        "claim_text": extraction.get("claim_text"),
        "evidence_status": gate.get("evidence_status"),
        "allowed_usage": gate.get("allowed_usage"),
        "usable_for_expectation_gap": bool(gate.get("usable_for_expectation_gap")),
        "usable_for_valuation_support": bool(gate.get("usable_for_valuation_support")),
        "usable_for_promotion": False,
        "limitations": extraction.get("limitations") or gate.get("downgrade_reasons") or [],
        "payload": {
            "gate": gate,
            "source_metadata": metadata,
            "raw_source_text_written": False,
        },
    }


def candidates_from_pipeline(row: dict[str, Any]) -> list[dict[str, Any]]:
    chunks_by_id = {f"{chunk.get('source_id')}:{chunk.get('chunk_id')}": chunk for chunk in row.get("chunks") or []}
    candidates = []
    seen = set()
    for gate in row.get("gate_results") or []:
        candidate = gate_result_to_candidate(gate, chunk=chunks_by_id.get(f"{gate.get('source_id')}:{gate.get('chunk_id')}"))
        if not candidate:
            continue
        key = (candidate["source_id"], candidate["chunk_id"], candidate["quoted_span"])
        if key in seen:
            continue
        seen.add(key)
        candidates.append(candidate)
    return candidates


def build_semantic_evidence_candidates(
    conn: sqlite3.Connection,
    tickers: str | None = None,
    *,
    use_real_sources: bool = True,
    allow_mock_fallback: bool = True,
    mode: str = "mock",
) -> dict[str, Any]:
    resolved = resolve_phase25_tickers(tickers)
    rows = []
    for ticker in resolved:
        pipeline = build_semantic_pipeline_for_ticker(
            ticker,
            mode=mode,
            conn=conn,
            use_real_sources=use_real_sources,
            allow_mock_fallback=allow_mock_fallback,
        )
        candidates = candidates_from_pipeline(pipeline)
        rows.append({"ticker": ticker, "pipeline": pipeline, "evidence_candidates": candidates})
    return {
        "generated_at": now_ts(),
        "summary": {
            "tickers_checked": len(rows),
            "semantic_evidence_candidates": sum(len(row["evidence_candidates"]) for row in rows),
            "raw_source_text_written": False,
        },
        "rows": rows,
    }


def write_semantic_evidence_candidates(conn: sqlite3.Connection, candidates: list[dict[str, Any]]) -> int:
    ensure_semantic_evidence_candidate_table(conn)
    now = now_ts()
    written = 0
    for candidate in candidates:
        if not candidate.get("source_url") or not candidate.get("quoted_span"):
            continue
        conn.execute(
            """
            INSERT INTO semantic_evidence_candidates (
                evidence_id, ticker, theme, source_id, source_url, source_type,
                chunk_id, quoted_span, variable_type, claim_text, evidence_status,
                allowed_usage, usable_for_expectation_gap, usable_for_valuation_support,
                usable_for_promotion, limitations_json, payload_json, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(evidence_id) DO UPDATE SET
                evidence_status=excluded.evidence_status,
                allowed_usage=excluded.allowed_usage,
                usable_for_expectation_gap=excluded.usable_for_expectation_gap,
                usable_for_valuation_support=excluded.usable_for_valuation_support,
                usable_for_promotion=excluded.usable_for_promotion,
                limitations_json=excluded.limitations_json,
                payload_json=excluded.payload_json,
                updated_at=excluded.updated_at
            """,
            (
                candidate.get("evidence_id"),
                candidate.get("ticker"),
                candidate.get("theme"),
                candidate.get("source_id"),
                candidate.get("source_url"),
                candidate.get("source_type"),
                candidate.get("chunk_id"),
                candidate.get("quoted_span"),
                candidate.get("variable_type"),
                candidate.get("claim_text"),
                candidate.get("evidence_status"),
                candidate.get("allowed_usage"),
                int(bool(candidate.get("usable_for_expectation_gap"))),
                int(bool(candidate.get("usable_for_valuation_support"))),
                0,
                json.dumps(candidate.get("limitations") or [], ensure_ascii=False),
                json.dumps(candidate.get("payload") or {}, ensure_ascii=False),
                now,
                now,
            ),
        )
        written += 1
    return written


def semantic_candidates_to_gate_results(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for candidate in candidates:
        rows.append(
            {
                "source_id": candidate.get("source_id"),
                "chunk_id": candidate.get("chunk_id"),
                "variable_type": candidate.get("variable_type"),
                "evidence_status": candidate.get("evidence_status"),
                "allowed_usage": candidate.get("allowed_usage"),
                "usable_for_expectation_gap": candidate.get("usable_for_expectation_gap"),
                "usable_for_valuation_support": candidate.get("usable_for_valuation_support"),
                "usable_for_promotion": False,
                "confidence_after_gate": "low_to_medium" if candidate.get("evidence_status") == "partial" else "low",
                "downgrade_reasons": candidate.get("limitations") or [],
                "extraction": {
                    "ticker": candidate.get("ticker"),
                    "theme": candidate.get("theme"),
                    "source_type": candidate.get("source_type"),
                    "quoted_span": candidate.get("quoted_span"),
                    "claim_text": candidate.get("claim_text"),
                    "limitations": candidate.get("limitations") or [],
                },
            }
        )
    return rows


def flatten_candidates(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [candidate for row in payload.get("rows") or [] for candidate in row.get("evidence_candidates") or []]
