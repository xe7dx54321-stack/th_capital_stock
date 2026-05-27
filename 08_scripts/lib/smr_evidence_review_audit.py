#!/usr/bin/env python3
"""Append-only evidence review audit log for Phase 31."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from typing import Any

from smr_evidence_lifecycle import dumps_json, loads_json
from smr_wiki import now_ts


def ensure_evidence_review_audit_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS evidence_review_audit_log (
            audit_id TEXT PRIMARY KEY,
            evidence_id TEXT NOT NULL,
            ticker TEXT,
            action TEXT NOT NULL,
            actor TEXT NOT NULL,
            mode TEXT NOT NULL,
            before_status TEXT,
            after_status TEXT,
            before_allowed_usage TEXT,
            after_allowed_usage TEXT,
            reason TEXT,
            quoted_span_preview TEXT,
            metadata_json TEXT NOT NULL DEFAULT '{}',
            promotion_allowed_after_action INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_evidence_review_audit_evidence
        ON evidence_review_audit_log(evidence_id, created_at DESC)
        """
    )


def audit_id_for(evidence_id: str, action: str, created_at: str, reason: str | None = None) -> str:
    raw = "|".join([str(evidence_id or ""), str(action or ""), str(created_at or ""), str(reason or "")])
    return "audit_ev_review_" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:18]


def preview_text(text: str | None, limit: int = 220) -> str:
    return " ".join(str(text or "").split())[:limit]


def write_evidence_review_audit(
    conn: sqlite3.Connection,
    *,
    evidence_id: str,
    ticker: str | None,
    action: str,
    actor: str = "system",
    mode: str,
    before: dict[str, Any] | None,
    after: dict[str, Any] | None,
    reason: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ensure_evidence_review_audit_table(conn)
    created_at = now_ts()
    before = before or {}
    after = after or {}
    audit_id = audit_id_for(evidence_id, action, created_at, reason)
    quoted_preview = after.get("quoted_span_preview") or before.get("quoted_span_preview") or preview_text(after.get("quoted_span") or before.get("quoted_span"))
    promotion_allowed = bool(after.get("usable_for_promotion"))
    conn.execute(
        """
        INSERT INTO evidence_review_audit_log (
            audit_id, evidence_id, ticker, action, actor, mode,
            before_status, after_status, before_allowed_usage, after_allowed_usage,
            reason, quoted_span_preview, metadata_json,
            promotion_allowed_after_action, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
        """,
        (
            audit_id,
            evidence_id,
            ticker,
            action,
            actor or "system",
            mode,
            before.get("lifecycle_status"),
            after.get("lifecycle_status"),
            before.get("allowed_usage"),
            after.get("allowed_usage"),
            reason,
            quoted_preview,
            dumps_json({**(metadata or {}), "promotion_allowed_requested": promotion_allowed}),
            created_at,
        ),
    )
    return get_audit_record(conn, audit_id) or {
        "audit_id": audit_id,
        "evidence_id": evidence_id,
        "ticker": ticker,
        "action": action,
        "actor": actor,
        "mode": mode,
        "created_at": created_at,
        "promotion_allowed_after_action": False,
    }


def get_audit_record(conn: sqlite3.Connection, audit_id: str) -> dict[str, Any] | None:
    ensure_evidence_review_audit_table(conn)
    row = conn.execute(
        """
        SELECT audit_id, evidence_id, ticker, action, actor, mode, before_status,
               after_status, before_allowed_usage, after_allowed_usage, reason,
               quoted_span_preview, metadata_json, promotion_allowed_after_action,
               created_at
        FROM evidence_review_audit_log
        WHERE audit_id = ?
        LIMIT 1
        """,
        (audit_id,),
    ).fetchone()
    return _row_to_audit(row) if row else None


def _row_to_audit(row: sqlite3.Row | tuple[Any, ...]) -> dict[str, Any]:
    return {
        "audit_id": row[0],
        "evidence_id": row[1],
        "ticker": row[2],
        "action": row[3],
        "actor": row[4],
        "mode": row[5],
        "before_status": row[6],
        "after_status": row[7],
        "before_allowed_usage": row[8],
        "after_allowed_usage": row[9],
        "reason": row[10],
        "quoted_span_preview": row[11],
        "metadata": loads_json(row[12], {}),
        "promotion_allowed_after_action": bool(row[13]),
        "created_at": row[14],
    }


def list_evidence_review_audits(conn: sqlite3.Connection, *, ticker: str | None = None, evidence_id: str | None = None) -> list[dict[str, Any]]:
    ensure_evidence_review_audit_table(conn)
    clauses = []
    params: list[Any] = []
    if ticker:
        clauses.append("ticker = ?")
        params.append(ticker)
    if evidence_id:
        clauses.append("evidence_id = ?")
        params.append(evidence_id)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = conn.execute(
        f"""
        SELECT audit_id, evidence_id, ticker, action, actor, mode, before_status,
               after_status, before_allowed_usage, after_allowed_usage, reason,
               quoted_span_preview, metadata_json, promotion_allowed_after_action,
               created_at
        FROM evidence_review_audit_log
        {where}
        ORDER BY created_at DESC, audit_id DESC
        """,
        tuple(params),
    ).fetchall()
    return [_row_to_audit(row) for row in rows]


def summarize_audits(audits: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "audit_records": len(audits),
        "promotion_allowed_true": sum(1 for row in audits if row.get("promotion_allowed_after_action")),
        "execute_actions": sum(1 for row in audits if row.get("mode") == "execute"),
        "dry_run_actions": sum(1 for row in audits if row.get("mode") == "dry_run"),
    }
