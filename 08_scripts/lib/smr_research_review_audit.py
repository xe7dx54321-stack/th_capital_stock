#!/usr/bin/env python3
"""Append-only audit log for Phase 40 research-review actions."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from smr_research_review_lifecycle import normalize_ticker
from smr_wiki import generate_execution_id, now_ts


def dumps_json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, sort_keys=True, default=str)


def loads_json(raw: str | None, fallback: Any) -> Any:
    if raw in (None, ""):
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback


def ensure_research_review_audit_table(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS research_review_audit_log (
            audit_id TEXT PRIMARY KEY,
            ticker TEXT NOT NULL,
            review_candidate_id TEXT NOT NULL,
            action TEXT NOT NULL,
            actor TEXT NOT NULL,
            mode TEXT NOT NULL,
            before_status TEXT NOT NULL,
            after_status TEXT NOT NULL,
            reason TEXT,
            created_at TEXT NOT NULL,
            promotion_allowed_after_action INTEGER NOT NULL DEFAULT 0,
            pending_created INTEGER NOT NULL DEFAULT 0,
            paper_order_created INTEGER NOT NULL DEFAULT 0,
            metadata_json TEXT NOT NULL DEFAULT '{}'
        );

        CREATE INDEX IF NOT EXISTS idx_research_review_audit_ticker
        ON research_review_audit_log(ticker, created_at DESC);

        CREATE INDEX IF NOT EXISTS idx_research_review_audit_action
        ON research_review_audit_log(action, created_at DESC);
        """
    )


def _row_to_dict(row: sqlite3.Row | tuple[Any, ...] | None) -> dict[str, Any]:
    if not row:
        return {}
    keys = [
        "audit_id",
        "ticker",
        "review_candidate_id",
        "action",
        "actor",
        "mode",
        "before_status",
        "after_status",
        "reason",
        "created_at",
        "promotion_allowed_after_action",
        "pending_created",
        "paper_order_created",
        "metadata_json",
    ]
    data = dict(zip(keys, row))
    data["promotion_allowed_after_action"] = bool(data.get("promotion_allowed_after_action"))
    data["pending_created"] = bool(data.get("pending_created"))
    data["paper_order_created"] = bool(data.get("paper_order_created"))
    data["metadata"] = loads_json(data.pop("metadata_json"), {})
    return data


def write_audit_record(
    conn: sqlite3.Connection,
    *,
    ticker: str,
    review_candidate_id: str,
    action: str,
    actor: str = "human_or_system",
    mode: str = "execute",
    before_status: str,
    after_status: str,
    reason: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ensure_research_review_audit_table(conn)
    audit_id = generate_execution_id(f"audit_research_review_{normalize_ticker(ticker).split('.')[0]}")
    conn.execute(
        """
        INSERT INTO research_review_audit_log (
            audit_id, ticker, review_candidate_id, action, actor, mode,
            before_status, after_status, reason, created_at,
            promotion_allowed_after_action, pending_created, paper_order_created,
            metadata_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            audit_id,
            normalize_ticker(ticker),
            review_candidate_id,
            action,
            actor or "human_or_system",
            mode,
            before_status,
            after_status,
            reason,
            now_ts(),
            0,
            0,
            0,
            dumps_json(metadata or {}),
        ),
    )
    return get_audit_record(conn, audit_id)


def get_audit_record(conn: sqlite3.Connection, audit_id: str) -> dict[str, Any]:
    ensure_research_review_audit_table(conn)
    row = conn.execute(
        """
        SELECT audit_id, ticker, review_candidate_id, action, actor, mode,
               before_status, after_status, reason, created_at,
               promotion_allowed_after_action, pending_created, paper_order_created,
               metadata_json
        FROM research_review_audit_log
        WHERE audit_id=?
        LIMIT 1
        """,
        (audit_id,),
    ).fetchone()
    return _row_to_dict(row)


def list_audit_records(conn: sqlite3.Connection, ticker: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    ensure_research_review_audit_table(conn)
    params: list[Any] = []
    where = ""
    if ticker:
        where = "WHERE ticker=?"
        params.append(normalize_ticker(ticker))
    rows = conn.execute(
        f"""
        SELECT audit_id, ticker, review_candidate_id, action, actor, mode,
               before_status, after_status, reason, created_at,
               promotion_allowed_after_action, pending_created, paper_order_created,
               metadata_json
        FROM research_review_audit_log
        {where}
        ORDER BY datetime(created_at) DESC, audit_id DESC
        LIMIT ?
        """,
        (*params, max(1, int(limit or 100))),
    ).fetchall()
    return [_row_to_dict(row) for row in rows]
