#!/usr/bin/env python3
"""Persistent history for live multi-ticker validation runs."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Any

from smr_registry import ensure_task_registry_tables, register_snapshot
from smr_wiki import now_ts


def ensure_live_run_history_tables(conn: sqlite3.Connection) -> None:
    ensure_task_registry_tables(conn)
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS phase_live_run_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT UNIQUE NOT NULL,
            run_time TEXT NOT NULL,
            watchlist_id TEXT NOT NULL,
            ticker_count INTEGER NOT NULL DEFAULT 0,
            pending_count INTEGER NOT NULL DEFAULT 0,
            candidate_shadow_count INTEGER NOT NULL DEFAULT 0,
            observation_count INTEGER NOT NULL DEFAULT 0,
            blocked_count INTEGER NOT NULL DEFAULT 0,
            failed_count INTEGER NOT NULL DEFAULT 0,
            per_ticker_status_json TEXT NOT NULL DEFAULT '{}',
            blocking_factors_json TEXT NOT NULL DEFAULT '{}',
            comparison_json TEXT NOT NULL DEFAULT '{}',
            summary_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_phase_live_run_history_watchlist_time
        ON phase_live_run_history(watchlist_id, run_time DESC, id DESC);
        """
    )


def loads_json(raw: str | None, fallback: Any) -> Any:
    if raw in (None, ""):
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback


def _count_bucket(ticker_rows: list[dict[str, Any]], *statuses: str) -> int:
    wanted = {status.lower() for status in statuses}
    return sum(1 for item in ticker_rows if str(item.get("status") or "").lower() in wanted)


def record_live_run_history(
    conn: sqlite3.Connection,
    *,
    run_id: str,
    watchlist_id: str,
    ticker_rows: list[dict[str, Any]],
    comparison: dict[str, Any] | None = None,
    summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ensure_live_run_history_tables(conn)
    run_time = now_ts()
    per_ticker_status = {
        str(item.get("ticker") or f"ticker_{index}"): {
            "status": item.get("status"),
            "action": item.get("action"),
            "summary_bucket": item.get("summary_bucket"),
            "blocking_factors": (item.get("promotion_debugger") or {}).get("blocking_factors") or [],
            "minimum_fix_path": (item.get("promotion_debugger") or {}).get("minimum_fix_path") or [],
            "missing_requirements": item.get("missing_requirements") or [],
        }
        for index, item in enumerate(ticker_rows, start=1)
    }
    blocking_factors: dict[str, list[dict[str, Any]]] = {}
    for item in ticker_rows:
        ticker = str(item.get("ticker") or "").upper()
        factors = (item.get("promotion_debugger") or {}).get("blocking_factors") or []
        if not factors:
            factors = (item.get("portfolio_risk") or {}).get("blocking_factors") or []
        blocking_factors[ticker] = factors
    pending_count = _count_bucket(ticker_rows, "pending_human_review")
    candidate_shadow_count = _count_bucket(ticker_rows, "candidate_shadow")
    observation_count = _count_bucket(ticker_rows, "observation_only", "observation", "watch")
    blocked_count = _count_bucket(ticker_rows, "blocked_by_data", "blocked_by_evidence")
    failed_count = _count_bucket(ticker_rows, "failed")
    payload = {
        "run_id": run_id,
        "run_time": run_time,
        "watchlist_id": watchlist_id,
        "ticker_count": len(ticker_rows),
        "pending_count": pending_count,
        "candidate_shadow_count": candidate_shadow_count,
        "observation_count": observation_count,
        "blocked_count": blocked_count,
        "failed_count": failed_count,
        "per_ticker_status": per_ticker_status,
        "blocking_factors": blocking_factors,
        "comparison": comparison or {},
        "summary": summary or {},
    }
    conn.execute(
        """
        INSERT INTO phase_live_run_history (
            run_id, run_time, watchlist_id, ticker_count, pending_count, candidate_shadow_count,
            observation_count, blocked_count, failed_count, per_ticker_status_json,
            blocking_factors_json, comparison_json, summary_json, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(run_id) DO UPDATE SET
            run_time=excluded.run_time,
            watchlist_id=excluded.watchlist_id,
            ticker_count=excluded.ticker_count,
            pending_count=excluded.pending_count,
            candidate_shadow_count=excluded.candidate_shadow_count,
            observation_count=excluded.observation_count,
            blocked_count=excluded.blocked_count,
            failed_count=excluded.failed_count,
            per_ticker_status_json=excluded.per_ticker_status_json,
            blocking_factors_json=excluded.blocking_factors_json,
            comparison_json=excluded.comparison_json,
            summary_json=excluded.summary_json,
            created_at=excluded.created_at
        """,
        (
            run_id,
            run_time,
            watchlist_id,
            len(ticker_rows),
            pending_count,
            candidate_shadow_count,
            observation_count,
            blocked_count,
            failed_count,
            json.dumps(per_ticker_status, ensure_ascii=False, sort_keys=True, default=str),
            json.dumps(blocking_factors, ensure_ascii=False, sort_keys=True, default=str),
            json.dumps(comparison or {}, ensure_ascii=False, sort_keys=True, default=str),
            json.dumps(summary or {}, ensure_ascii=False, sort_keys=True, default=str),
            run_time,
        ),
    )
    register_snapshot(
        conn,
        entity_type="phase_live_run_history",
        entity_id=run_id,
        status=str((summary or {}).get("overall_result") or "recorded"),
        source="smr_live_run_history",
        payload=payload,
    )
    return payload


def list_live_run_history(conn: sqlite3.Connection, watchlist_id: str | None = None, limit: int = 10) -> list[dict[str, Any]]:
    ensure_live_run_history_tables(conn)
    params: list[Any] = []
    where = []
    if watchlist_id:
        where.append("watchlist_id=?")
        params.append(watchlist_id)
    where_sql = f"WHERE {' AND '.join(where)}" if where else ""
    rows = conn.execute(
        f"""
        SELECT run_id, run_time, watchlist_id, ticker_count, pending_count, candidate_shadow_count,
               observation_count, blocked_count, failed_count, per_ticker_status_json,
               blocking_factors_json, comparison_json, summary_json, created_at
        FROM phase_live_run_history
        {where_sql}
        ORDER BY datetime(run_time) DESC, id DESC
        LIMIT ?
        """,
        (*params, limit),
    ).fetchall()
    results = []
    for row in rows:
        results.append(
            {
                "run_id": row[0],
                "run_time": row[1],
                "watchlist_id": row[2],
                "ticker_count": row[3],
                "pending_count": row[4],
                "candidate_shadow_count": row[5],
                "observation_count": row[6],
                "blocked_count": row[7],
                "failed_count": row[8],
                "per_ticker_status": loads_json(row[9], {}),
                "blocking_factors": loads_json(row[10], {}),
                "comparison": loads_json(row[11], {}),
                "summary": loads_json(row[12], {}),
                "created_at": row[13],
            }
        )
    return results


def latest_live_run_history(conn: sqlite3.Connection, watchlist_id: str | None = None) -> dict[str, Any]:
    rows = list_live_run_history(conn, watchlist_id=watchlist_id, limit=1)
    return rows[0] if rows else {}


def compare_live_run_history(previous: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    prev_status = previous.get("per_ticker_status") or {}
    curr_status = current.get("per_ticker_status") or {}
    improved: list[str] = []
    worsened: list[str] = []
    unchanged: list[str] = []
    repeated_blockers: dict[str, list[str]] = {}
    for ticker, current_item in curr_status.items():
        previous_item = prev_status.get(ticker) or {}
        current_status = str(current_item.get("status") or "")
        previous_status = str(previous_item.get("status") or "")
        if previous_status and previous_status != current_status:
            if previous_status in {"observation_only", "observation", "watch", "candidate_shadow"} and current_status == "pending_human_review":
                improved.append(ticker)
            elif previous_status == "pending_human_review" and current_status != "pending_human_review":
                worsened.append(ticker)
            elif current_status not in {previous_status}:
                if current_status in {"pending_human_review", "candidate_shadow"}:
                    improved.append(ticker)
                else:
                    worsened.append(ticker)
        elif previous_status == current_status:
            unchanged.append(ticker)
        blockers = [str(item.get("code") or item.get("detail") or "").strip() for item in (current_item.get("blocking_factors") or []) if item]
        if blockers:
            repeated_blockers[ticker] = blockers
    return {
        "previous_run_id": previous.get("run_id"),
        "current_run_id": current.get("run_id"),
        "improved": improved,
        "worsened": worsened,
        "unchanged": unchanged,
        "repeated_blockers": repeated_blockers,
        "pending_delta": int(current.get("pending_count") or 0) - int(previous.get("pending_count") or 0),
        "candidate_shadow_delta": int(current.get("candidate_shadow_count") or 0) - int(previous.get("candidate_shadow_count") or 0),
        "observation_delta": int(current.get("observation_count") or 0) - int(previous.get("observation_count") or 0),
        "blocked_delta": int(current.get("blocked_count") or 0) - int(previous.get("blocked_count") or 0),
        "failed_delta": int(current.get("failed_count") or 0) - int(previous.get("failed_count") or 0),
    }
