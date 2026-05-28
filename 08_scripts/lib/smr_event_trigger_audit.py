#!/usr/bin/env python3
"""Phase 48 event trigger audit log."""

from __future__ import annotations

import sqlite3
from typing import Any

from smr_paper_watchlist_entry import dumps_json, loads_json
from smr_research_review_lifecycle import normalize_ticker
from smr_wiki import generate_execution_id, now_ts


def ensure_event_trigger_audit_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS phase48_event_trigger_audit_log (
            audit_id TEXT PRIMARY KEY,
            ticker TEXT NOT NULL,
            event_id TEXT NOT NULL,
            action TEXT NOT NULL,
            before_watchlist_status TEXT NOT NULL,
            after_watchlist_status TEXT NOT NULL,
            thesis_delta TEXT NOT NULL DEFAULT 'unchanged',
            pending_created INTEGER NOT NULL DEFAULT 0,
            paper_order_created INTEGER NOT NULL DEFAULT 0,
            real_trade_created INTEGER NOT NULL DEFAULT 0,
            metadata_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_phase48_event_audit_ticker
        ON phase48_event_trigger_audit_log(ticker, created_at DESC)
        """
    )


def write_event_trigger_audit(
    conn: sqlite3.Connection,
    *,
    ticker: str,
    event_id: str,
    action: str = "event_driven_research_refresh",
    before_watchlist_status: str,
    after_watchlist_status: str,
    thesis_delta: str = "unchanged",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ensure_event_trigger_audit_table(conn)
    audit_id = generate_execution_id(f"audit_event_refresh_{normalize_ticker(ticker).split('.')[0]}")
    conn.execute(
        """
        INSERT INTO phase48_event_trigger_audit_log (
            audit_id, ticker, event_id, action,
            before_watchlist_status, after_watchlist_status,
            thesis_delta, pending_created, paper_order_created, real_trade_created,
            metadata_json, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            audit_id, normalize_ticker(ticker), event_id, action,
            before_watchlist_status, after_watchlist_status,
            thesis_delta, 0, 0, 0,
            dumps_json(metadata or {}), now_ts(),
        ),
    )
    return get_event_trigger_audit(conn, audit_id)


def _row_to_record(row: sqlite3.Row | tuple[Any, ...]) -> dict[str, Any]:
    return {
        "audit_id": row[0], "ticker": row[1], "event_id": row[2],
        "action": row[3], "before_watchlist_status": row[4],
        "after_watchlist_status": row[5], "thesis_delta": row[6],
        "pending_created": bool(row[7]), "paper_order_created": bool(row[8]),
        "real_trade_created": bool(row[9]), "metadata": loads_json(row[10], {}),
        "created_at": row[11],
    }


def get_event_trigger_audit(conn: sqlite3.Connection, audit_id: str) -> dict[str, Any]:
    ensure_event_trigger_audit_table(conn)
    row = conn.execute(
        """
        SELECT audit_id, ticker, event_id, action,
               before_watchlist_status, after_watchlist_status,
               thesis_delta, pending_created, paper_order_created, real_trade_created,
               metadata_json, created_at
        FROM phase48_event_trigger_audit_log
        WHERE audit_id=? LIMIT 1
        """, (audit_id,),
    ).fetchone()
    return _row_to_record(row) if row else {}


def list_event_trigger_audits(
    conn: sqlite3.Connection, ticker: str | None = None
) -> list[dict[str, Any]]:
    ensure_event_trigger_audit_table(conn)
    params: list[Any] = []
    where = ""
    if ticker:
        where = "WHERE ticker=?"
        params.append(normalize_ticker(ticker))
    rows = conn.execute(
        f"""
        SELECT audit_id, ticker, event_id, action,
               before_watchlist_status, after_watchlist_status,
               thesis_delta, pending_created, paper_order_created, real_trade_created,
               metadata_json, created_at
        FROM phase48_event_trigger_audit_log
        {where}
        ORDER BY datetime(created_at) DESC, audit_id DESC
        """, params,
    ).fetchall()
    return [_row_to_record(row) for row in rows]
