#!/usr/bin/env python3
"""Phase 43 manual intake rejection records."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from smr_research_review_lifecycle import normalize_ticker
from smr_wiki import now_ts


def dumps_json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, sort_keys=True, default=str)


def loads_json(raw: Any, fallback: Any) -> Any:
    if raw in (None, ""):
        return fallback
    if isinstance(raw, (dict, list)):
        return raw
    try:
        return json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return fallback


def ensure_manual_intake_rejection_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS manual_intake_rejections (
            rejection_id TEXT PRIMARY KEY,
            ticker TEXT NOT NULL,
            intake_id TEXT NOT NULL,
            evidence_type TEXT NOT NULL,
            rejection_reasons_json TEXT NOT NULL DEFAULT '[]',
            recommended_fix TEXT NOT NULL,
            payload_json TEXT NOT NULL DEFAULT '{}',
            pending_created INTEGER NOT NULL DEFAULT 0,
            paper_order_created INTEGER NOT NULL DEFAULT 0,
            promotion_allowed INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_manual_intake_rejections_intake
        ON manual_intake_rejections(intake_id)
        """
    )


def rejection_id_for(intake_id: str) -> str:
    value = str(intake_id or "manual_intake_unknown")
    if value.startswith("manual_intake_"):
        return value.replace("manual_intake_", "manual_reject_", 1)
    return f"manual_reject_{value}"


def recommended_fix_for(evidence_type: str, reasons: list[str]) -> str:
    reason_set = set(reasons)
    if evidence_type == "official_consensus":
        if "internal_proxy_cannot_be_official_consensus" in reason_set or "official_consensus_requires_authorized_source" in reason_set:
            return "provide authorized consensus source metadata"
        if "source_provider_required" in reason_set:
            return "provide the authorized source provider"
        if "source_date_required" in reason_set:
            return "provide the source date"
    if evidence_type == "supplier_share":
        return "provide direct company/customer disclosure or keep as explicit scenario assumption"
    if evidence_type == "confirmed_customer_allocation":
        return "provide direct company disclosure or customer-side public allocation statement"
    if "source_url_or_reference_required" in reason_set:
        return "provide a source URL or auditable manual reference"
    if "quoted_span_required" in reason_set:
        return "provide a quoted span or auditable assumption note"
    return "provide complete, permitted manual source metadata"


def build_rejection_record(payload: dict[str, Any], reasons: list[str]) -> dict[str, Any]:
    evidence_type = str(payload.get("evidence_type") or "")
    intake_id = str(payload.get("intake_id") or "manual_intake_unknown")
    return {
        "rejection_id": rejection_id_for(intake_id),
        "ticker": normalize_ticker(str(payload.get("ticker") or "")),
        "intake_id": intake_id,
        "evidence_type": evidence_type,
        "rejection_reasons": list(dict.fromkeys(reasons)),
        "recommended_fix": recommended_fix_for(evidence_type, reasons),
        "created_at": now_ts(),
        "pending_created": False,
        "paper_order_created": False,
        "promotion_allowed": False,
        "payload": {
            "manual_payload": payload,
            "bad_input_not_silently_ignored": True,
        },
    }


def write_rejection_records(conn: sqlite3.Connection, records: list[dict[str, Any]]) -> dict[str, int]:
    ensure_manual_intake_rejection_table(conn)
    written = 0
    duplicates = 0
    for record in records:
        existing = conn.execute(
            "SELECT rejection_id FROM manual_intake_rejections WHERE rejection_id=? LIMIT 1",
            (record.get("rejection_id"),),
        ).fetchone()
        if existing:
            duplicates += 1
            continue
        conn.execute(
            """
            INSERT INTO manual_intake_rejections (
                rejection_id, ticker, intake_id, evidence_type, rejection_reasons_json,
                recommended_fix, payload_json, pending_created, paper_order_created,
                promotion_allowed, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.get("rejection_id"),
                record.get("ticker"),
                record.get("intake_id"),
                record.get("evidence_type"),
                dumps_json(record.get("rejection_reasons") or []),
                record.get("recommended_fix"),
                dumps_json(record.get("payload") or {}),
                0,
                0,
                0,
                record.get("created_at") or now_ts(),
            ),
        )
        written += 1
    return {"written": written, "duplicates_skipped": duplicates}


def _row_to_record(row: sqlite3.Row | tuple[Any, ...]) -> dict[str, Any]:
    return {
        "rejection_id": row[0],
        "ticker": row[1],
        "intake_id": row[2],
        "evidence_type": row[3],
        "rejection_reasons": loads_json(row[4], []),
        "recommended_fix": row[5],
        "payload": loads_json(row[6], {}),
        "pending_created": bool(row[7]),
        "paper_order_created": bool(row[8]),
        "promotion_allowed": bool(row[9]),
        "created_at": row[10],
    }


def list_rejection_records(conn: sqlite3.Connection, ticker: str | None = None) -> list[dict[str, Any]]:
    ensure_manual_intake_rejection_table(conn)
    params: list[Any] = []
    where = ""
    if ticker:
        where = "WHERE ticker=?"
        params.append(normalize_ticker(ticker))
    rows = conn.execute(
        f"""
        SELECT rejection_id, ticker, intake_id, evidence_type, rejection_reasons_json,
               recommended_fix, payload_json, pending_created, paper_order_created,
               promotion_allowed, created_at
        FROM manual_intake_rejections
        {where}
        ORDER BY datetime(created_at) DESC, rejection_id
        """,
        params,
    ).fetchall()
    return [_row_to_record(row) for row in rows]
