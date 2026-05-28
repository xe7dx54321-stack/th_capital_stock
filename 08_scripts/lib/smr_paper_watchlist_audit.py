#!/usr/bin/env python3
"""Phase 46 paper watchlist audit log."""

from __future__ import annotations

import sqlite3
from typing import Any

from smr_paper_watchlist_entry import dumps_json, loads_json
from smr_research_review_lifecycle import normalize_ticker
from smr_wiki import generate_execution_id, now_ts


def ensure_paper_watchlist_audit_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS phase46_paper_watchlist_audit_log (
            audit_id TEXT PRIMARY KEY,
            ticker TEXT NOT NULL,
            action TEXT NOT NULL,
            before_status TEXT NOT NULL,
            after_status TEXT NOT NULL,
            source_phase TEXT NOT NULL,
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
        CREATE INDEX IF NOT EXISTS idx_phase46_watchlist_audit_ticker
        ON phase46_paper_watchlist_audit_log(ticker, created_at DESC)
        """
    )


def write_paper_watchlist_audit(
    conn: sqlite3.Connection,
    *,
    ticker: str,
    action: str,
    before_status: str,
    after_status: str,
    source_phase: str = "phase45",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ensure_paper_watchlist_audit_table(conn)
    audit_id = generate_execution_id(f"audit_paper_watchlist_{normalize_ticker(ticker).split('.')[0]}")
    conn.execute(
        """
        INSERT INTO phase46_paper_watchlist_audit_log (
            audit_id, ticker, action, before_status, after_status, source_phase,
            pending_created, paper_order_created, real_trade_created, metadata_json, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            audit_id,
            normalize_ticker(ticker),
            action,
            before_status,
            after_status,
            source_phase,
            0,
            0,
            0,
            dumps_json(metadata or {}),
            now_ts(),
        ),
    )
    return get_paper_watchlist_audit(conn, audit_id)


def _row_to_record(row: sqlite3.Row | tuple[Any, ...]) -> dict[str, Any]:
    return {
        "audit_id": row[0],
        "ticker": row[1],
        "action": row[2],
        "before_status": row[3],
        "after_status": row[4],
        "source_phase": row[5],
        "pending_created": bool(row[6]),
        "paper_order_created": bool(row[7]),
        "real_trade_created": bool(row[8]),
        "metadata": loads_json(row[9], {}),
        "created_at": row[10],
    }


def get_paper_watchlist_audit(conn: sqlite3.Connection, audit_id: str) -> dict[str, Any]:
    ensure_paper_watchlist_audit_table(conn)
    row = conn.execute(
        """
        SELECT audit_id, ticker, action, before_status, after_status, source_phase,
               pending_created, paper_order_created, real_trade_created, metadata_json, created_at
        FROM phase46_paper_watchlist_audit_log
        WHERE audit_id=?
        LIMIT 1
        """,
        (audit_id,),
    ).fetchone()
    return _row_to_record(row) if row else {}


def list_paper_watchlist_audits(conn: sqlite3.Connection, ticker: str | None = None) -> list[dict[str, Any]]:
    ensure_paper_watchlist_audit_table(conn)
    params: list[Any] = []
    where = ""
    if ticker:
        where = "WHERE ticker=?"
        params.append(normalize_ticker(ticker))
    rows = conn.execute(
        f"""
        SELECT audit_id, ticker, action, before_status, after_status, source_phase,
               pending_created, paper_order_created, real_trade_created, metadata_json, created_at
        FROM phase46_paper_watchlist_audit_log
        {where}
        ORDER BY datetime(created_at) DESC, audit_id DESC
        """,
        params,
    ).fetchall()
    return [_row_to_record(row) for row in rows]
