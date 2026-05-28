#!/usr/bin/env python3
"""Phase 47 paper watchlist periodic review state management."""

from __future__ import annotations

import sqlite3
from typing import Any

from smr_paper_watchlist_entry import (
    dumps_json,
    loads_json,
    get_paper_watchlist_entry,
    ensure_paper_watchlist_entry_table,
    TRACKING_MODE,
)
from smr_paper_watchlist_lifecycle import WATCHLIST_STATUSES
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import generate_execution_id, now_ts


REVIEW_STATUSES = {
    "review_due",
    "review_completed",
    "review_skipped_no_change",
    "review_needs_more_evidence",
    "review_strengthened",
    "review_weakened",
    "review_archive_candidate",
    "unknown",
}

REVIEW_CADENCES = {
    "weekly",
    "on_new_evidence",
    "manual",
    "monthly",
    "weekly_or_on_new_evidence",
}

DEFAULT_REVIEW_CADENCE = "weekly_or_on_new_evidence"


def ensure_periodic_review_state_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS phase47_periodic_review_state (
            review_state_id TEXT PRIMARY KEY,
            ticker TEXT NOT NULL,
            watchlist_entry_id TEXT NOT NULL,
            watchlist_status_before_review TEXT NOT NULL,
            review_status TEXT NOT NULL,
            review_cadence TEXT NOT NULL,
            last_reviewed_at TEXT,
            next_review_reason TEXT NOT NULL DEFAULT '',
            pending_allowed INTEGER NOT NULL DEFAULT 0,
            paper_order_allowed INTEGER NOT NULL DEFAULT 0,
            real_trade_allowed INTEGER NOT NULL DEFAULT 0,
            thesis_delta TEXT NOT NULL DEFAULT 'unchanged',
            new_evidence_found INTEGER NOT NULL DEFAULT 0,
            metadata_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_phase47_review_state_ticker
        ON phase47_periodic_review_state(ticker, review_status, updated_at DESC)
        """
    )


def build_periodic_review_state(
    conn: sqlite3.Connection | None = None,
    ticker: str = TARGET_REVIEW_TICKER,
    *,
    review_status: str = "review_due",
    review_cadence: str = "weekly_or_on_new_evidence",
    next_review_reason: str = "first_periodic_review_after_watchlist_entry",
) -> dict[str, Any]:
    ticker = normalize_ticker(ticker)
    if review_status not in REVIEW_STATUSES:
        review_status = "review_due"
    if review_cadence not in REVIEW_CADENCES:
        review_cadence = DEFAULT_REVIEW_CADENCE
    watchlist_status = "active_tracking"
    watchlist_entry_id = ""
    if conn is not None:
        entry = get_paper_watchlist_entry(conn, ticker)
        if entry:
            watchlist_status = entry.get("watchlist_status") or watchlist_status
            watchlist_entry_id = entry.get("watchlist_entry_id") or watchlist_entry_id
    return {
        "ticker": ticker,
        "watchlist_entry_id": watchlist_entry_id,
        "watchlist_status_before_review": watchlist_status,
        "review_status": review_status,
        "review_cadence": review_cadence,
        "last_reviewed_at": None,
        "next_review_reason": next_review_reason,
        "pending_allowed": False,
        "paper_order_allowed": False,
        "real_trade_allowed": False,
        "thesis_delta": "unchanged",
        "new_evidence_found": False,
    }


def _row_to_review_state(row: sqlite3.Row | tuple[Any, ...]) -> dict[str, Any]:
    return {
        "review_state_id": row[0],
        "ticker": row[1],
        "watchlist_entry_id": row[2],
        "watchlist_status_before_review": row[3],
        "review_status": row[4],
        "review_cadence": row[5],
        "last_reviewed_at": row[6],
        "next_review_reason": row[7],
        "pending_allowed": bool(row[8]),
        "paper_order_allowed": bool(row[9]),
        "real_trade_allowed": bool(row[10]),
        "thesis_delta": row[11],
        "new_evidence_found": bool(row[12]),
        "metadata": loads_json(row[13], {}),
        "created_at": row[14],
        "updated_at": row[15],
    }


def get_periodic_review_state(conn: sqlite3.Connection, ticker: str) -> dict[str, Any] | None:
    ensure_periodic_review_state_table(conn)
    row = conn.execute(
        """
        SELECT review_state_id, ticker, watchlist_entry_id,
               watchlist_status_before_review, review_status, review_cadence,
               last_reviewed_at, next_review_reason,
               pending_allowed, paper_order_allowed, real_trade_allowed,
               thesis_delta, new_evidence_found, metadata_json, created_at, updated_at
        FROM phase47_periodic_review_state
        WHERE ticker=?
        ORDER BY datetime(updated_at) DESC
        LIMIT 1
        """,
        (normalize_ticker(ticker),),
    ).fetchone()
    return _row_to_review_state(row) if row else None


def upsert_periodic_review_state(
    conn: sqlite3.Connection,
    *,
    ticker: str = TARGET_REVIEW_TICKER,
    review_status: str = "review_due",
    review_cadence: str = "weekly_or_on_new_evidence",
    next_review_reason: str = "",
    thesis_delta: str = "unchanged",
    new_evidence_found: bool = False,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ticker = normalize_ticker(ticker)
    ensure_periodic_review_state_table(conn)
    existing = get_periodic_review_state(conn, ticker)
    now = now_ts()
    base = build_periodic_review_state(
        conn, ticker,
        review_status=review_status,
        review_cadence=review_cadence,
        next_review_reason=next_review_reason,
    )
    state_id = (existing or {}).get("review_state_id") or generate_execution_id(
        f"review_state_{ticker.split('.')[0]}"
    )
    created_at = (existing or {}).get("created_at") or now
    merged_metadata = {
        **((existing or {}).get("metadata") or {}),
        **(metadata or {}),
    }
    conn.execute(
        """
        INSERT INTO phase47_periodic_review_state (
            review_state_id, ticker, watchlist_entry_id,
            watchlist_status_before_review, review_status, review_cadence,
            last_reviewed_at, next_review_reason,
            pending_allowed, paper_order_allowed, real_trade_allowed,
            thesis_delta, new_evidence_found, metadata_json, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(review_state_id) DO UPDATE SET
            ticker=excluded.ticker,
            watchlist_entry_id=excluded.watchlist_entry_id,
            watchlist_status_before_review=excluded.watchlist_status_before_review,
            review_status=excluded.review_status,
            review_cadence=excluded.review_cadence,
            last_reviewed_at=excluded.last_reviewed_at,
            next_review_reason=excluded.next_review_reason,
            pending_allowed=excluded.pending_allowed,
            paper_order_allowed=excluded.paper_order_allowed,
            real_trade_allowed=excluded.real_trade_allowed,
            thesis_delta=excluded.thesis_delta,
            new_evidence_found=excluded.new_evidence_found,
            metadata_json=excluded.metadata_json,
            updated_at=excluded.updated_at
        """,
        (
            state_id,
            ticker,
            base["watchlist_entry_id"],
            base["watchlist_status_before_review"],
            review_status,
            review_cadence,
            None,
            next_review_reason,
            0,
            0,
            0,
            thesis_delta,
            1 if new_evidence_found else 0,
            dumps_json(merged_metadata),
            created_at,
            now,
        ),
    )
    updated = get_periodic_review_state(conn, ticker) or {}
    updated["entry_created"] = existing is None
    updated["entry_updated"] = existing is not None
    return updated
