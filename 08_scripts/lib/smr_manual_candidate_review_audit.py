#!/usr/bin/env python3
"""Phase 44 manual candidate review audit log."""

from __future__ import annotations

import sqlite3
from typing import Any

from smr_manual_candidate_review_lifecycle import dumps_json, loads_json
from smr_research_review_lifecycle import normalize_ticker
from smr_wiki import generate_execution_id, now_ts


def ensure_manual_candidate_review_audit_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS manual_candidate_review_audit_log (
            audit_id TEXT PRIMARY KEY,
            ticker TEXT NOT NULL,
            candidate_id TEXT NOT NULL,
            candidate_type TEXT NOT NULL,
            action TEXT NOT NULL,
            before_status TEXT NOT NULL,
            after_status TEXT NOT NULL,
            confirmation_status_after_action TEXT NOT NULL,
            allowed_usage_after_action TEXT NOT NULL,
            usable_for_promotion INTEGER NOT NULL DEFAULT 0,
            pending_created INTEGER NOT NULL DEFAULT 0,
            paper_order_created INTEGER NOT NULL DEFAULT 0,
            metadata_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_manual_candidate_review_audit_ticker
        ON manual_candidate_review_audit_log(ticker, created_at DESC)
        """
    )


def write_manual_candidate_review_audit(
    conn: sqlite3.Connection,
    *,
    ticker: str,
    candidate_id: str,
    candidate_type: str,
    action: str,
    before_status: str,
    after_status: str,
    confirmation_status_after_action: str,
    allowed_usage_after_action: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ensure_manual_candidate_review_audit_table(conn)
    audit_id = generate_execution_id(f"audit_manual_candidate_review_{normalize_ticker(ticker).split('.')[0]}")
    conn.execute(
        """
        INSERT INTO manual_candidate_review_audit_log (
            audit_id, ticker, candidate_id, candidate_type, action, before_status,
            after_status, confirmation_status_after_action, allowed_usage_after_action,
            usable_for_promotion, pending_created, paper_order_created,
            metadata_json, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            audit_id,
            normalize_ticker(ticker),
            candidate_id,
            candidate_type,
            action,
            before_status,
            after_status,
            confirmation_status_after_action,
            allowed_usage_after_action,
            0,
            0,
            0,
            dumps_json(metadata or {}),
            now_ts(),
        ),
    )
    return get_manual_candidate_review_audit(conn, audit_id)


def _row_to_record(row: sqlite3.Row | tuple[Any, ...]) -> dict[str, Any]:
    return {
        "audit_id": row[0],
        "ticker": row[1],
        "candidate_id": row[2],
        "candidate_type": row[3],
        "action": row[4],
        "before_status": row[5],
        "after_status": row[6],
        "confirmation_status_after_action": row[7],
        "allowed_usage_after_action": row[8],
        "usable_for_promotion": bool(row[9]),
        "pending_created": bool(row[10]),
        "paper_order_created": bool(row[11]),
        "metadata": loads_json(row[12], {}),
        "created_at": row[13],
    }


def get_manual_candidate_review_audit(conn: sqlite3.Connection, audit_id: str) -> dict[str, Any]:
    ensure_manual_candidate_review_audit_table(conn)
    row = conn.execute(
        """
        SELECT audit_id, ticker, candidate_id, candidate_type, action, before_status,
               after_status, confirmation_status_after_action, allowed_usage_after_action,
               usable_for_promotion, pending_created, paper_order_created,
               metadata_json, created_at
        FROM manual_candidate_review_audit_log
        WHERE audit_id=?
        LIMIT 1
        """,
        (audit_id,),
    ).fetchone()
    return _row_to_record(row) if row else {}


def list_manual_candidate_review_audits(conn: sqlite3.Connection, ticker: str | None = None) -> list[dict[str, Any]]:
    ensure_manual_candidate_review_audit_table(conn)
    params: list[Any] = []
    where = ""
    if ticker:
        where = "WHERE ticker=?"
        params.append(normalize_ticker(ticker))
    rows = conn.execute(
        f"""
        SELECT audit_id, ticker, candidate_id, candidate_type, action, before_status,
               after_status, confirmation_status_after_action, allowed_usage_after_action,
               usable_for_promotion, pending_created, paper_order_created,
               metadata_json, created_at
        FROM manual_candidate_review_audit_log
        {where}
        ORDER BY datetime(created_at) DESC, audit_id DESC
        """,
        params,
    ).fetchall()
    return [_row_to_record(row) for row in rows]
