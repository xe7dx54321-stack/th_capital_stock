#!/usr/bin/env python3
"""Phase 46 paper watchlist entry schema and persistence."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from smr_final_research_asset_aggregator import company_name_for_ticker
from smr_final_research_conclusion import build_final_research_conclusion
from smr_paper_watchlist_lifecycle import WATCHLIST_STATUSES, validate_watchlist_transition
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts


TRACKING_MODE = "research_only_tracking"


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


def watchlist_entry_id_for_ticker(ticker: str) -> str:
    return f"paper_watchlist_{normalize_ticker(ticker).lower().replace('.', '_')}_phase46"


def build_paper_watchlist_entry(
    conn: sqlite3.Connection | None = None,
    ticker: str = TARGET_REVIEW_TICKER,
    *,
    status: str = "paper_watchlist_candidate",
) -> dict[str, Any]:
    ticker = normalize_ticker(ticker)
    conclusion_status = "formal_research_conclusion_positive_watchlist"
    if conn is not None:
        conclusion = build_final_research_conclusion(conn, ticker).get("final_research_conclusion") or {}
        conclusion_status = conclusion.get("conclusion_status") or conclusion_status
    if status not in WATCHLIST_STATUSES:
        status = "unknown"
    return {
        "ticker": ticker,
        "company_name": company_name_for_ticker(ticker),
        "watchlist_entry_id": watchlist_entry_id_for_ticker(ticker),
        "source_phase": "phase45",
        "source_conclusion_status": conclusion_status,
        "watchlist_status": status,
        "tracking_mode": TRACKING_MODE,
        "paper_watchlist_allowed": True,
        "pending_human_review_allowed": False,
        "paper_order_allowed": False,
        "real_trade_allowed": False,
        "created_from_research_packet": True,
        "created_at": now_ts(),
    }


def ensure_paper_watchlist_entry_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS phase46_paper_watchlist_entries (
            watchlist_entry_id TEXT PRIMARY KEY,
            ticker TEXT NOT NULL,
            company_name TEXT,
            source_phase TEXT NOT NULL,
            source_conclusion_status TEXT NOT NULL,
            watchlist_status TEXT NOT NULL,
            tracking_mode TEXT NOT NULL,
            paper_watchlist_allowed INTEGER NOT NULL DEFAULT 1,
            pending_human_review_allowed INTEGER NOT NULL DEFAULT 0,
            paper_order_allowed INTEGER NOT NULL DEFAULT 0,
            real_trade_allowed INTEGER NOT NULL DEFAULT 0,
            created_from_research_packet INTEGER NOT NULL DEFAULT 1,
            metadata_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_phase46_paper_watchlist_ticker
        ON phase46_paper_watchlist_entries(ticker, watchlist_status, updated_at DESC)
        """
    )


def _row_to_entry(row: sqlite3.Row | tuple[Any, ...]) -> dict[str, Any]:
    return {
        "watchlist_entry_id": row[0],
        "ticker": row[1],
        "company_name": row[2],
        "source_phase": row[3],
        "source_conclusion_status": row[4],
        "watchlist_status": row[5],
        "tracking_mode": row[6],
        "paper_watchlist_allowed": bool(row[7]),
        "pending_human_review_allowed": bool(row[8]),
        "paper_order_allowed": bool(row[9]),
        "real_trade_allowed": bool(row[10]),
        "created_from_research_packet": bool(row[11]),
        "metadata": loads_json(row[12], {}),
        "created_at": row[13],
        "updated_at": row[14],
    }


def get_paper_watchlist_entry(conn: sqlite3.Connection, ticker: str) -> dict[str, Any] | None:
    ensure_paper_watchlist_entry_table(conn)
    row = conn.execute(
        """
        SELECT watchlist_entry_id, ticker, company_name, source_phase,
               source_conclusion_status, watchlist_status, tracking_mode,
               paper_watchlist_allowed, pending_human_review_allowed,
               paper_order_allowed, real_trade_allowed, created_from_research_packet,
               metadata_json, created_at, updated_at
        FROM phase46_paper_watchlist_entries
        WHERE ticker=?
        LIMIT 1
        """,
        (normalize_ticker(ticker),),
    ).fetchone()
    return _row_to_entry(row) if row else None


def list_paper_watchlist_entries(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    ensure_paper_watchlist_entry_table(conn)
    rows = conn.execute(
        """
        SELECT watchlist_entry_id, ticker, company_name, source_phase,
               source_conclusion_status, watchlist_status, tracking_mode,
               paper_watchlist_allowed, pending_human_review_allowed,
               paper_order_allowed, real_trade_allowed, created_from_research_packet,
               metadata_json, created_at, updated_at
        FROM phase46_paper_watchlist_entries
        ORDER BY ticker
        """
    ).fetchall()
    return [_row_to_entry(row) for row in rows]


def upsert_paper_watchlist_entry(
    conn: sqlite3.Connection,
    *,
    ticker: str = TARGET_REVIEW_TICKER,
    status: str = "active_tracking",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ticker = normalize_ticker(ticker)
    ensure_paper_watchlist_entry_table(conn)
    existing = get_paper_watchlist_entry(conn, ticker)
    before_status = (existing or {}).get("watchlist_status") or "paper_watchlist_candidate"
    effective_status = status
    if existing and status == "active_tracking" and before_status not in {"paper_watchlist_candidate", "tracking_paused", "tracking_needs_more_evidence"}:
        effective_status = before_status
    ok, reason = validate_watchlist_transition(before_status, effective_status)
    if not ok:
        raise ValueError(reason)
    base = build_paper_watchlist_entry(conn, ticker, status=effective_status)
    now = now_ts()
    created_at = (existing or {}).get("created_at") or now
    merged_metadata = {
        **((existing or {}).get("metadata") or {}),
        **(metadata or {}),
        "watchlist_entry_is_pending": False,
        "watchlist_entry_is_paper_position": False,
            "promotion_gate_connected": False,
        }
    conn.execute(
        """
        INSERT INTO phase46_paper_watchlist_entries (
            watchlist_entry_id, ticker, company_name, source_phase,
            source_conclusion_status, watchlist_status, tracking_mode,
            paper_watchlist_allowed, pending_human_review_allowed,
            paper_order_allowed, real_trade_allowed, created_from_research_packet,
            metadata_json, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(watchlist_entry_id) DO UPDATE SET
            company_name=excluded.company_name,
            source_phase=excluded.source_phase,
            source_conclusion_status=excluded.source_conclusion_status,
            watchlist_status=excluded.watchlist_status,
            tracking_mode=excluded.tracking_mode,
            paper_watchlist_allowed=1,
            pending_human_review_allowed=0,
            paper_order_allowed=0,
            real_trade_allowed=0,
            created_from_research_packet=1,
            metadata_json=excluded.metadata_json,
            updated_at=excluded.updated_at
        """,
        (
            base["watchlist_entry_id"],
            ticker,
            base["company_name"],
            base["source_phase"],
            base["source_conclusion_status"],
            effective_status,
            base["tracking_mode"],
            1,
            0,
            0,
            0,
            1,
            dumps_json(merged_metadata),
            created_at,
            now,
        ),
    )
    updated = get_paper_watchlist_entry(conn, ticker) or {}
    updated["before_status"] = before_status
    updated["entry_created"] = existing is None
    updated["entry_updated"] = existing is not None and before_status != effective_status
    updated["duplicate_skipped"] = existing is not None and before_status == effective_status
    updated["requested_status"] = status
    updated["effective_status"] = effective_status
    return updated
