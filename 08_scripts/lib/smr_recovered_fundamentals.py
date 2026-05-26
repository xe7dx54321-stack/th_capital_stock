#!/usr/bin/env python3
"""Integrate recovered financial statement fields into fundamentals snapshots."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from smr_cninfo_table_parser import extract_income_statement_fields_from_chunks
from smr_fundamentals import (
    FUNDAMENTAL_FIELDS,
    ensure_fundamentals_tables,
    latest_fundamentals_snapshot,
    market_for_ticker,
    upsert_fundamentals_evidence,
)
from smr_hkex_table_parser import extract_shareholders_equity_from_chunks
from smr_wiki import generate_execution_id, now_ts


TARGET_FIELDS_BY_MARKET = {
    "H": ["shareholders_equity"],
    "A": ["revenue", "gross_profit"],
}


def loads_json(raw: str | None, fallback: Any) -> Any:
    if raw in (None, ""):
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback


def financial_statement_chunks(conn: sqlite3.Connection, ticker: str, *, limit: int = 48) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT chunk_id, text, evidence_id, chunk_section_type, created_at, metadata_json
        FROM document_chunks
        WHERE ticker=?
          AND evidence_id IS NOT NULL
          AND COALESCE(chunk_section_type, '') IN ('income_statement', 'balance_sheet', 'cash_flow_statement', 'financial_highlights')
        ORDER BY datetime(created_at) DESC, chunk_index ASC
        LIMIT ?
        """,
        (ticker.upper(), limit),
    ).fetchall() if conn.execute("SELECT 1 FROM sqlite_master WHERE type IN ('table','view') AND name='document_chunks'").fetchone() else []
    chunks: list[dict[str, Any]] = []
    for chunk_id, text, evidence_id, section_type, created_at, metadata_json in rows:
        metadata = loads_json(metadata_json, {})
        chunks.append(
            {
                "chunk_id": chunk_id,
                "text": text,
                "evidence_id": evidence_id,
                "chunk_section_type": section_type,
                "section_type": section_type,
                "created_at": created_at,
                "published_at": metadata.get("published_at") or metadata.get("period") or created_at,
                "source_id": metadata.get("source_id"),
                "source_url": metadata.get("source_url"),
            }
        )
    return chunks


def recovered_fields_from_chunks(conn: sqlite3.Connection, ticker: str) -> dict[str, dict[str, Any]]:
    ticker = ticker.upper()
    chunks = financial_statement_chunks(conn, ticker)
    market = market_for_ticker(ticker)
    recovered: dict[str, dict[str, Any]] = {}
    if market == "H":
        detail = extract_shareholders_equity_from_chunks(chunks, ticker=ticker, market="H")
        if detail.get("status") == "extracted":
            recovered["shareholders_equity"] = detail
    elif market == "A":
        result = extract_income_statement_fields_from_chunks(chunks, ticker=ticker)
        for field in ("revenue", "gross_profit"):
            detail = (result.get("field_status") or {}).get(field) or {}
            if detail.get("status") in {"extracted", "derived"}:
                recovered[field] = detail
    return recovered


def _field_is_usable_for_snapshot(detail: dict[str, Any]) -> bool:
    if detail.get("status") == "extracted":
        return detail.get("extracted_value") is not None and bool(detail.get("source_evidence_id"))
    if detail.get("status") == "derived":
        return detail.get("extracted_value") is not None and bool(detail.get("input_evidence_ids"))
    return False


def _field_evidence_ids(detail: dict[str, Any]) -> list[str]:
    ids = []
    ids.extend([str(item) for item in detail.get("source_evidence_ids") or [] if item])
    if detail.get("source_evidence_id"):
        ids.append(str(detail["source_evidence_id"]))
    ids.extend([str(item) for item in detail.get("input_evidence_ids") or [] if item])
    return list(dict.fromkeys(ids))


def field_recovered_in_snapshot(field: str, snapshot: dict[str, Any]) -> bool:
    detail = (snapshot.get("field_details") or {}).get(field) or {}
    if snapshot.get(field) is None:
        return False
    evidence_ids = _field_evidence_ids(detail)
    if not evidence_ids:
        return False
    if detail.get("allowed_usage") in {"blocked", "context_only"}:
        return False
    if float(detail.get("confidence") or 0.0) < 0.6:
        return False
    return True


def update_fundamentals_from_recovered_chunks(conn: sqlite3.Connection, ticker: str) -> dict[str, Any]:
    ticker = ticker.upper()
    ensure_fundamentals_tables(conn)
    previous = latest_fundamentals_snapshot(conn, ticker) or {}
    recovered = recovered_fields_from_chunks(conn, ticker)
    market = market_for_ticker(ticker)
    target_fields = TARGET_FIELDS_BY_MARKET.get(market or "", [])
    values = {field: previous.get(field) for field in FUNDAMENTAL_FIELDS}
    field_details = dict(previous.get("field_details") or {})
    missing_fields = set(previous.get("missing_fields") or FUNDAMENTAL_FIELDS)
    missing_reasons = dict(previous.get("field_missing_reasons") or {})
    source_evidence_ids = list(previous.get("source_evidence_ids") or [])
    fields_updated: list[dict[str, Any]] = []
    fields_skipped: list[dict[str, Any]] = []

    for field in target_fields:
        detail = dict(recovered.get(field) or {})
        if not detail:
            fields_skipped.append({"field": field, "reason": "recovered_field_not_found"})
            continue
        if not _field_is_usable_for_snapshot(detail):
            fields_skipped.append({"field": field, "reason": "recovered_field_not_traceable", "status": detail.get("status")})
            continue
        previous_detail = dict(field_details.get(field) or {})
        previous_value = values.get(field)
        values[field] = detail.get("extracted_value")
        detail["previous_value"] = previous_value
        detail["previous_detail"] = previous_detail
        detail["phase18_recovered"] = True
        detail["allowed_usage"] = detail.get("allowed_usage") or "supporting_evidence"
        field_details[field] = detail
        missing_fields.discard(field)
        missing_reasons.pop(field, None)
        evidence_ids = _field_evidence_ids(detail)
        source_evidence_ids.extend(evidence_ids)
        fields_updated.append(
            {
                "field": field,
                "status": detail.get("status"),
                "source_evidence_id": detail.get("source_evidence_id"),
                "input_evidence_ids": detail.get("input_evidence_ids") or [],
                "allowed_usage": detail.get("allowed_usage"),
                "previous_value": previous_value,
                "value": values[field],
            }
        )

    source_evidence_ids = list(dict.fromkeys(item for item in source_evidence_ids if item))
    snapshot_id = generate_execution_id("fundamentals")
    created_at = now_ts()
    metadata = {
        **(previous.get("metadata") or {}),
        "phase18_recovered_fields": fields_updated,
        "phase18_fields_skipped": fields_skipped,
        "previous_snapshot_id": previous.get("snapshot_id"),
    }
    present_count = len([field for field in FUNDAMENTAL_FIELDS if values.get(field) is not None])
    confidence = round(max(float(previous.get("confidence") or 0.0), max([float((field_details.get(field) or {}).get("confidence") or 0.0) for field in target_fields] or [0.0])), 3)
    freshness_status = previous.get("freshness_status") or ("degraded" if fields_updated else "missing")
    if fields_updated and freshness_status == "missing":
        freshness_status = "degraded"
    snapshot = {
        "snapshot_id": snapshot_id,
        "ticker": ticker,
        "market": market,
        "period": previous.get("period"),
        "fiscal_year": previous.get("fiscal_year"),
        "fiscal_quarter": previous.get("fiscal_quarter"),
        **values,
        "source_evidence_ids": source_evidence_ids,
        "source_quality": "primary" if source_evidence_ids else (previous.get("source_quality") or "missing"),
        "freshness_status": freshness_status,
        "confidence": confidence if present_count else 0.0,
        "missing_fields": sorted(missing_fields),
        "field_details": field_details,
        "field_missing_reasons": missing_reasons,
        "created_at": created_at,
        "metadata": metadata,
    }
    conn.execute(
        f"""
        INSERT INTO fundamentals_snapshot (
            snapshot_id, ticker, market, period, fiscal_year, fiscal_quarter,
            {', '.join(FUNDAMENTAL_FIELDS)},
            source_evidence_ids_json, source_quality, freshness_status, confidence,
            missing_fields_json, field_details_json, field_missing_reasons_json, created_at, metadata_json
        )
        VALUES (
            ?, ?, ?, ?, ?, ?,
            {', '.join('?' for _ in FUNDAMENTAL_FIELDS)},
            ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
        """,
        (
            snapshot_id,
            ticker,
            market,
            snapshot["period"],
            snapshot["fiscal_year"],
            snapshot["fiscal_quarter"],
            *[snapshot.get(field) for field in FUNDAMENTAL_FIELDS],
            json.dumps(snapshot["source_evidence_ids"], ensure_ascii=False),
            snapshot["source_quality"],
            snapshot["freshness_status"],
            snapshot["confidence"],
            json.dumps(snapshot["missing_fields"], ensure_ascii=False),
            json.dumps(snapshot["field_details"], ensure_ascii=False, sort_keys=True, default=str),
            json.dumps(snapshot["field_missing_reasons"], ensure_ascii=False, sort_keys=True, default=str),
            created_at,
            json.dumps(snapshot["metadata"], ensure_ascii=False, sort_keys=True, default=str),
        ),
    )
    evidence_id = upsert_fundamentals_evidence(conn, ticker, snapshot)
    snapshot["fundamentals_evidence_id"] = evidence_id
    return {
        "ticker": ticker,
        "fundamentals_snapshot_update": {
            "status": "updated" if fields_updated else "no_recovered_fields",
            "snapshot_id": snapshot_id,
            "previous_snapshot_id": previous.get("snapshot_id"),
            "fields_updated": fields_updated,
            "fields_skipped": fields_skipped,
            "missing_fields_after": snapshot["missing_fields"],
        },
        "snapshot": snapshot,
    }
