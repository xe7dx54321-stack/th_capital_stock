#!/usr/bin/env python3
"""Download-unavailable source repair queue for Phase 31."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections import Counter
from typing import Any

from smr_evidence_lifecycle import dumps_json, loads_json
from smr_wiki import now_ts


REPAIR_TASK_TYPES = {
    "IR_SOURCE_DOWNLOAD_UNAVAILABLE",
    "MANUAL_TEXT_NEEDED",
    "ALTERNATE_SOURCE_NEEDED",
    "OPTIONAL_OCR_NEEDED",
    "SOURCE_MARKED_UNAVAILABLE",
}

REPAIR_STATUSES = {"open", "in_progress", "resolved", "ignored", "blocked"}

ACTION_TO_TASK_TYPE = {
    "retry_with_headers_or_alt_url": "IR_SOURCE_DOWNLOAD_UNAVAILABLE",
    "manual_text_needed": "MANUAL_TEXT_NEEDED",
    "alternate_source_needed": "ALTERNATE_SOURCE_NEEDED",
    "mark_unavailable": "SOURCE_MARKED_UNAVAILABLE",
    "needs_ocr_optional": "OPTIONAL_OCR_NEEDED",
}


def ensure_download_repair_tasks_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS download_repair_tasks (
            repair_task_id TEXT PRIMARY KEY,
            source_id TEXT NOT NULL,
            ticker TEXT NOT NULL,
            task_type TEXT NOT NULL,
            priority TEXT NOT NULL,
            source_url TEXT,
            reason TEXT,
            recommended_action TEXT,
            status TEXT NOT NULL DEFAULT 'open',
            metadata_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_download_repair_source_task
        ON download_repair_tasks(source_id, task_type)
        """
    )


def repair_task_id_for(source_id: str, task_type: str) -> str:
    raw = "|".join([str(source_id or ""), str(task_type or "")])
    return "repair_download_ir_" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def task_type_for_action(action: str | None) -> str:
    return ACTION_TO_TASK_TYPE.get(str(action or ""), "IR_SOURCE_DOWNLOAD_UNAVAILABLE")


def normalize_repair_task(source: dict[str, Any]) -> dict[str, Any]:
    task_type = str(source.get("task_type") or task_type_for_action(source.get("repair_action") or source.get("recommended_action")))
    if task_type not in REPAIR_TASK_TYPES:
        task_type = "IR_SOURCE_DOWNLOAD_UNAVAILABLE"
    source_id = str(source.get("source_id") or source.get("evidence_id") or "unknown_source")
    return {
        "repair_task_id": source.get("repair_task_id") or repair_task_id_for(source_id, task_type),
        "source_id": source_id,
        "ticker": str(source.get("ticker") or "UNKNOWN").upper(),
        "task_type": task_type,
        "priority": source.get("priority") or "medium",
        "source_url": source.get("source_url"),
        "reason": source.get("reason") or source.get("failure_reason") or source.get("detail"),
        "recommended_action": source.get("recommended_action") or source.get("repair_action") or "manual_text_needed",
        "status": source.get("status") or "open",
        "metadata": {
            "phase": 31,
            "auto_download_bypass": False,
            "ocr_default_enabled": False,
            "manual_text_needed_is_not_evidence": True,
            **(source.get("metadata") or {}),
        },
    }


def upsert_download_repair_task(conn: sqlite3.Connection, source: dict[str, Any]) -> dict[str, Any]:
    ensure_download_repair_tasks_table(conn)
    task = normalize_repair_task(source)
    if task["task_type"] not in REPAIR_TASK_TYPES:
        raise ValueError(f"invalid repair task type: {task['task_type']}")
    if task["status"] not in REPAIR_STATUSES:
        task["status"] = "open"
    now = now_ts()
    existing = get_download_repair_task(conn, task["repair_task_id"])
    created_at = (existing or {}).get("created_at") or now
    merged_metadata = {**((existing or {}).get("metadata") or {}), **(task.get("metadata") or {})}
    conn.execute(
        """
        INSERT INTO download_repair_tasks (
            repair_task_id, source_id, ticker, task_type, priority, source_url,
            reason, recommended_action, status, metadata_json, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(source_id, task_type) DO UPDATE SET
            priority=excluded.priority,
            source_url=excluded.source_url,
            reason=excluded.reason,
            recommended_action=excluded.recommended_action,
            status=download_repair_tasks.status,
            metadata_json=excluded.metadata_json,
            updated_at=excluded.updated_at
        """,
        (
            task["repair_task_id"],
            task["source_id"],
            task["ticker"],
            task["task_type"],
            task["priority"],
            task.get("source_url"),
            task.get("reason"),
            task.get("recommended_action"),
            task.get("status") or "open",
            dumps_json(merged_metadata),
            created_at,
            now,
        ),
    )
    return get_download_repair_task_by_source(conn, task["source_id"], task["task_type"]) or task


def get_download_repair_task(conn: sqlite3.Connection, repair_task_id: str) -> dict[str, Any] | None:
    ensure_download_repair_tasks_table(conn)
    row = conn.execute(
        """
        SELECT repair_task_id, source_id, ticker, task_type, priority, source_url,
               reason, recommended_action, status, metadata_json, created_at, updated_at
        FROM download_repair_tasks
        WHERE repair_task_id = ?
        LIMIT 1
        """,
        (repair_task_id,),
    ).fetchone()
    return _row_to_task(row) if row else None


def get_download_repair_task_by_source(conn: sqlite3.Connection, source_id: str, task_type: str) -> dict[str, Any] | None:
    ensure_download_repair_tasks_table(conn)
    row = conn.execute(
        """
        SELECT repair_task_id, source_id, ticker, task_type, priority, source_url,
               reason, recommended_action, status, metadata_json, created_at, updated_at
        FROM download_repair_tasks
        WHERE source_id = ? AND task_type = ?
        LIMIT 1
        """,
        (source_id, task_type),
    ).fetchone()
    return _row_to_task(row) if row else None


def _row_to_task(row: sqlite3.Row | tuple[Any, ...]) -> dict[str, Any]:
    return {
        "repair_task_id": row[0],
        "source_id": row[1],
        "ticker": row[2],
        "task_type": row[3],
        "priority": row[4],
        "source_url": row[5],
        "reason": row[6],
        "recommended_action": row[7],
        "status": row[8],
        "metadata": loads_json(row[9], {}),
        "created_at": row[10],
        "updated_at": row[11],
    }


def list_download_repair_tasks(conn: sqlite3.Connection, *, ticker: str | None = None) -> list[dict[str, Any]]:
    ensure_download_repair_tasks_table(conn)
    where = "WHERE ticker = ?" if ticker else ""
    params: tuple[Any, ...] = (ticker,) if ticker else ()
    rows = conn.execute(
        f"""
        SELECT repair_task_id, source_id, ticker, task_type, priority, source_url,
               reason, recommended_action, status, metadata_json, created_at, updated_at
        FROM download_repair_tasks
        {where}
        ORDER BY status, priority DESC, updated_at DESC
        """,
        params,
    ).fetchall()
    return [_row_to_task(row) for row in rows]


def summarize_download_repair_tasks(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    task_types = Counter(task.get("task_type") for task in tasks)
    statuses = Counter(task.get("status") for task in tasks)
    return {
        "repair_tasks_total": len(tasks),
        "open_tasks": statuses.get("open", 0),
        "manual_text_needed": task_types.get("MANUAL_TEXT_NEEDED", 0),
        "alternate_source_needed": task_types.get("ALTERNATE_SOURCE_NEEDED", 0),
        "optional_ocr_needed": task_types.get("OPTIONAL_OCR_NEEDED", 0),
        "download_unavailable": task_types.get("IR_SOURCE_DOWNLOAD_UNAVAILABLE", 0),
    }
