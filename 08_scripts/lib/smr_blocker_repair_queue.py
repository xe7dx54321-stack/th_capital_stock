#!/usr/bin/env python3
"""Repair queue for repeated Phase 8 live-pipeline blockers."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime
from typing import Any

from smr_blocker_taxonomy import normalize_blocker, priority_for_blocker


VALID_REPAIR_STATUSES = {"open", "in_progress", "resolved", "ignored", "needs_manual_review"}


def now_ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def loads_json(raw: str | None, fallback: Any) -> Any:
    if raw in (None, ""):
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback


def dumps_json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, sort_keys=True, default=str)


def ensure_blocker_repair_queue_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS phase_blocker_repair_queue (
            repair_id TEXT PRIMARY KEY,
            ticker TEXT NOT NULL,
            market TEXT,
            watchlist_id TEXT,
            blocker_code TEXT NOT NULL,
            blocker_type TEXT,
            priority TEXT NOT NULL,
            severity TEXT,
            fixability TEXT,
            expected_impact TEXT,
            suggested_fix TEXT,
            source_run_ids_json TEXT NOT NULL DEFAULT '[]',
            affected_fields_json TEXT NOT NULL DEFAULT '[]',
            status TEXT NOT NULL DEFAULT 'open',
            owner TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            resolved_at TEXT,
            metadata_json TEXT NOT NULL DEFAULT '{}'
        );

        CREATE INDEX IF NOT EXISTS idx_phase_blocker_repair_queue_status
        ON phase_blocker_repair_queue(status, priority, updated_at DESC);

        CREATE INDEX IF NOT EXISTS idx_phase_blocker_repair_queue_ticker_code
        ON phase_blocker_repair_queue(ticker, blocker_code, status);
        """
    )


def repair_id_for(ticker: str, blocker_code: str, watchlist_id: str | None = None) -> str:
    raw = "|".join([str(watchlist_id or "global"), str(ticker or "").upper(), str(blocker_code or "")])
    return "repair_" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:18]


def _merge_unique(left: list[Any], right: list[Any]) -> list[Any]:
    return list(dict.fromkeys([str(item) for item in [*(left or []), *(right or [])] if str(item).strip()]))


def _row_to_dict(row: sqlite3.Row | tuple[Any, ...]) -> dict[str, Any]:
    keys = [
        "repair_id",
        "ticker",
        "market",
        "watchlist_id",
        "blocker_code",
        "blocker_type",
        "priority",
        "severity",
        "fixability",
        "expected_impact",
        "suggested_fix",
        "source_run_ids_json",
        "affected_fields_json",
        "status",
        "owner",
        "created_at",
        "updated_at",
        "resolved_at",
        "metadata_json",
    ]
    data = dict(zip(keys, row))
    data["source_run_ids"] = loads_json(data.pop("source_run_ids_json"), [])
    data["affected_fields"] = loads_json(data.pop("affected_fields_json"), [])
    data["metadata"] = loads_json(data.pop("metadata_json"), {})
    return data


def upsert_repair_task(
    conn: sqlite3.Connection,
    ticker: str,
    market: str | None,
    watchlist_id: str | None,
    blocker_code: str,
    blocker_type: str | None,
    priority: str | None,
    severity: str | None,
    fixability: str | None,
    expected_impact: str | None,
    suggested_fix: str | None,
    source_run_ids: list[str],
    affected_fields: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ensure_blocker_repair_queue_tables(conn)
    normalized = normalize_blocker(
        {
            "code": blocker_code,
            "type": blocker_type,
            "severity": severity,
            "fixability": fixability,
            "suggested_fix": suggested_fix,
            "expected_impact": expected_impact,
            "affected_fields": affected_fields or [],
        }
    )
    normalized_priority = priority or priority_for_blocker(normalized)
    repair_id = repair_id_for(ticker, normalized["code"], watchlist_id)
    now = now_ts()
    existing = conn.execute(
        """
        SELECT repair_id, ticker, market, watchlist_id, blocker_code, blocker_type, priority,
               severity, fixability, expected_impact, suggested_fix, source_run_ids_json,
               affected_fields_json, status, owner, created_at, updated_at, resolved_at, metadata_json
        FROM phase_blocker_repair_queue
        WHERE repair_id=?
        LIMIT 1
        """,
        (repair_id,),
    ).fetchone()
    source_run_ids = [str(item) for item in source_run_ids or [] if str(item).strip()]
    affected_fields = [str(item) for item in affected_fields or normalized.get("affected_fields") or [] if str(item).strip()]
    task_metadata = dict(metadata or {})
    if existing:
        current = _row_to_dict(existing)
        source_run_ids = _merge_unique(current.get("source_run_ids") or [], source_run_ids)
        affected_fields = _merge_unique(current.get("affected_fields") or [], affected_fields)
        task_metadata = {**(current.get("metadata") or {}), **task_metadata}
        status = current.get("status") or "open"
        resolved_at = current.get("resolved_at")
        if status == "resolved" and task_metadata.get("reopened"):
            status = "open"
            resolved_at = None
    else:
        status = "open"
        resolved_at = None
    conn.execute(
        """
        INSERT INTO phase_blocker_repair_queue (
            repair_id, ticker, market, watchlist_id, blocker_code, blocker_type, priority,
            severity, fixability, expected_impact, suggested_fix, source_run_ids_json,
            affected_fields_json, status, owner, created_at, updated_at, resolved_at, metadata_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(repair_id) DO UPDATE SET
            market=excluded.market,
            blocker_type=excluded.blocker_type,
            priority=excluded.priority,
            severity=excluded.severity,
            fixability=excluded.fixability,
            expected_impact=excluded.expected_impact,
            suggested_fix=excluded.suggested_fix,
            source_run_ids_json=excluded.source_run_ids_json,
            affected_fields_json=excluded.affected_fields_json,
            status=excluded.status,
            updated_at=excluded.updated_at,
            resolved_at=excluded.resolved_at,
            metadata_json=excluded.metadata_json
        """,
        (
            repair_id,
            str(ticker or "").upper(),
            market,
            watchlist_id,
            normalized["code"],
            normalized["type"],
            normalized_priority,
            normalized["severity"],
            normalized["fixability"],
            normalized["expected_impact"],
            normalized["suggested_fix"],
            dumps_json(source_run_ids),
            dumps_json(affected_fields),
            status,
            (existing and _row_to_dict(existing).get("owner")) or None,
            (existing and _row_to_dict(existing).get("created_at")) or now,
            now,
            resolved_at,
            dumps_json(task_metadata),
        ),
    )
    return get_repair_task(conn, repair_id)


def get_repair_task(conn: sqlite3.Connection, repair_id: str) -> dict[str, Any]:
    ensure_blocker_repair_queue_tables(conn)
    row = conn.execute(
        """
        SELECT repair_id, ticker, market, watchlist_id, blocker_code, blocker_type, priority,
               severity, fixability, expected_impact, suggested_fix, source_run_ids_json,
               affected_fields_json, status, owner, created_at, updated_at, resolved_at, metadata_json
        FROM phase_blocker_repair_queue
        WHERE repair_id=?
        LIMIT 1
        """,
        (repair_id,),
    ).fetchone()
    return _row_to_dict(row) if row else {}


def list_repair_tasks(
    conn: sqlite3.Connection,
    status: str | None = None,
    ticker: str | None = None,
    watchlist_id: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    ensure_blocker_repair_queue_tables(conn)
    filters = []
    params: list[Any] = []
    if status:
        filters.append("status=?")
        params.append(status)
    if ticker:
        filters.append("ticker=?")
        params.append(ticker.upper())
    if watchlist_id:
        filters.append("watchlist_id=?")
        params.append(watchlist_id)
    where = "WHERE " + " AND ".join(filters) if filters else ""
    rows = conn.execute(
        f"""
        SELECT repair_id, ticker, market, watchlist_id, blocker_code, blocker_type, priority,
               severity, fixability, expected_impact, suggested_fix, source_run_ids_json,
               affected_fields_json, status, owner, created_at, updated_at, resolved_at, metadata_json
        FROM phase_blocker_repair_queue
        {where}
        ORDER BY
            CASE priority WHEN 'high' THEN 0 WHEN 'medium' THEN 1 ELSE 2 END,
            datetime(updated_at) DESC,
            repair_id
        LIMIT ?
        """,
        (*params, max(1, int(limit or 50))),
    ).fetchall()
    return [_row_to_dict(row) for row in rows]


def update_repair_task_status(
    conn: sqlite3.Connection,
    repair_id: str,
    status: str,
    owner: str | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    ensure_blocker_repair_queue_tables(conn)
    if status not in VALID_REPAIR_STATUSES:
        raise ValueError(f"Unsupported repair task status: {status}")
    current = get_repair_task(conn, repair_id)
    if not current:
        raise ValueError(f"Unknown repair task: {repair_id}")
    metadata = dict(current.get("metadata") or {})
    if note:
        metadata.setdefault("status_notes", []).append({"at": now_ts(), "status": status, "note": note})
    resolved_at = now_ts() if status == "resolved" else None
    conn.execute(
        """
        UPDATE phase_blocker_repair_queue
        SET status=?, owner=COALESCE(?, owner), updated_at=?, resolved_at=?, metadata_json=?
        WHERE repair_id=?
        """,
        (status, owner, now_ts(), resolved_at, dumps_json(metadata), repair_id),
    )
    return get_repair_task(conn, repair_id)


def update_repair_task_metadata(
    conn: sqlite3.Connection,
    repair_id: str,
    metadata_updates: dict[str, Any] | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    """Merge repair execution metadata without changing task status."""

    ensure_blocker_repair_queue_tables(conn)
    current = get_repair_task(conn, repair_id)
    if not current:
        raise ValueError(f"Unknown repair task: {repair_id}")
    metadata = dict(current.get("metadata") or {})
    metadata.update(metadata_updates or {})
    if note:
        metadata.setdefault("execution_notes", []).append({"at": now_ts(), "note": note})
    conn.execute(
        """
        UPDATE phase_blocker_repair_queue
        SET updated_at=?, metadata_json=?
        WHERE repair_id=?
        """,
        (now_ts(), dumps_json(metadata), repair_id),
    )
    return get_repair_task(conn, repair_id)


def resolve_repair_task_after_validation(
    conn: sqlite3.Connection,
    repair_id: str,
    *,
    validation_blockers: list[str],
    replacement_blockers: list[str] | None = None,
    reason: str | None = None,
    owner: str | None = "codex",
) -> dict[str, Any]:
    """Resolve only when validation proves the original blocker disappeared."""

    current = get_repair_task(conn, repair_id)
    if not current:
        raise ValueError(f"Unknown repair task: {repair_id}")
    blocker_code = str(current.get("blocker_code") or "")
    blockers = {str(item) for item in validation_blockers or []}
    replacements = [str(item) for item in replacement_blockers or [] if str(item).strip()]
    resolution_check = {
        "validation_blockers": sorted(blockers),
        "replacement_blockers": replacements,
        "umbrella_blocker_removed": blocker_code not in blockers,
        "is_resolved": blocker_code not in blockers and not replacements,
        "reason": reason,
    }
    update_repair_task_metadata(
        conn,
        repair_id,
        {"phase10_resolution_check": resolution_check},
        note=reason or "Phase 10 validation resolution check",
    )
    if resolution_check["is_resolved"]:
        return update_repair_task_status(conn, repair_id, "resolved", owner=owner, note=reason or "validated blocker disappeared")
    if blocker_code not in blockers and replacements:
        return update_repair_task_status(conn, repair_id, "in_progress", owner=owner, note=reason or "umbrella blocker split into sub-blockers")
    if reason and "not_applicable" in reason:
        return update_repair_task_status(conn, repair_id, "ignored", owner=owner, note=reason)
    return update_repair_task_status(conn, repair_id, "needs_manual_review", owner=owner, note=reason or "blocker remains after validation")


def apply_phase13_core_gate_metadata(
    conn: sqlite3.Connection,
    *,
    ticker: str,
    field_gate: dict[str, Any],
    data_quality_gate: dict[str, Any],
    watchlist_id: str | None = "ai_core",
    owner: str | None = "codex",
) -> dict[str, Any]:
    """Reflect Phase 13 core/non-core classification in repair queue metadata.

    Optional missing fields remain repair tasks, but are marked non-blocking
    rather than incorrectly resolved.
    """

    ensure_blocker_repair_queue_tables(conn)
    tasks = list_repair_tasks(conn, ticker=ticker, watchlist_id=watchlist_id, limit=200)
    optional_fields = {
        item.get("field")
        for item in (field_gate.get("optional_warnings") or [])
        if isinstance(item, dict) and item.get("field")
    }
    supporting_fields = {
        item.get("field")
        for item in (field_gate.get("supporting_warnings") or [])
        if isinstance(item, dict) and item.get("field")
    }
    core_fields = {
        item.get("field")
        for item in (field_gate.get("core_blockers") or [])
        if isinstance(item, dict) and item.get("field")
    }
    updated: list[dict[str, Any]] = []
    counters = {
        "optional_missing_marked_warning": 0,
        "supporting_missing_marked_in_progress": 0,
        "core_missing_still_open": 0,
    }
    for task in tasks:
        fields = set(str(item) for item in task.get("affected_fields") or [])
        metadata_updates: dict[str, Any] = {
            "phase13_core_gate": {
                "gate_status": field_gate.get("gate_status"),
                "data_quality_gate_status": data_quality_gate.get("status") or data_quality_gate.get("after_status"),
            }
        }
        if fields & optional_fields:
            counters["optional_missing_marked_warning"] += 1
            metadata_updates["non_blocking_warning"] = True
            metadata_updates["warning_classification"] = "optional_missing"
            task = update_repair_task_metadata(conn, task["repair_id"], metadata_updates, note="Phase 13 classified this missing field as optional warning")
            if task.get("status") == "open":
                task = update_repair_task_status(conn, task["repair_id"], "in_progress", owner=owner, note="optional missing is non-blocking but still tracked")
            updated.append(task)
        elif fields & supporting_fields:
            counters["supporting_missing_marked_in_progress"] += 1
            metadata_updates["warning_classification"] = "supporting_missing"
            task = update_repair_task_metadata(conn, task["repair_id"], metadata_updates, note="Phase 13 classified this missing field as supporting warning")
            if task.get("status") == "open":
                task = update_repair_task_status(conn, task["repair_id"], "in_progress", owner=owner, note="supporting missing remains repairable")
            updated.append(task)
        elif fields & core_fields:
            counters["core_missing_still_open"] += 1
            metadata_updates["warning_classification"] = "core_missing"
            metadata_updates["non_blocking_warning"] = False
            task = update_repair_task_metadata(conn, task["repair_id"], metadata_updates, note="Phase 13 confirmed this missing field is core-blocking")
            if task.get("status") != "open":
                task = update_repair_task_status(conn, task["repair_id"], "open", owner=owner, note="core missing remains blocking")
            updated.append(task)
    return {
        "ticker": ticker.upper(),
        "watchlist_id": watchlist_id,
        "tasks_considered": len(tasks),
        "tasks_updated": len(updated),
        "counters": counters,
        "updated_tasks": updated[:20],
    }
