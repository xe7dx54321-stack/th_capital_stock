#!/usr/bin/env python3
"""Phase 47 new evidence delta detector for watchlist periodic review."""

from __future__ import annotations

import sqlite3
from typing import Any

from smr_paper_watchlist_entry import loads_json
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts


def count_evidence_chains(conn: sqlite3.Connection, ticker: str) -> int:
    tbl = "semantic_evidence"
    try:
        row = conn.execute(
            "SELECT COUNT(*) FROM semantic_evidence WHERE ticker=?",
            (normalize_ticker(ticker),),
        ).fetchone()
        return row[0] if row else 0
    except sqlite3.OperationalError:
        return 0


def count_manual_candidates(conn: sqlite3.Connection, ticker: str) -> int:
    try:
        row = conn.execute(
            "SELECT COUNT(*) FROM phase44_manual_candidate_reviews WHERE ticker=?",
            (normalize_ticker(ticker),),
        ).fetchone()
        return row[0] if row else 0
    except sqlite3.OperationalError:
        return 0


def build_new_evidence_delta(
    conn: sqlite3.Connection,
    ticker: str = TARGET_REVIEW_TICKER,
) -> dict[str, Any]:
    ticker = normalize_ticker(ticker)
    evidence_count = count_evidence_chains(conn, ticker)
    manual_count = count_manual_candidates(conn, ticker)
    no_new = evidence_count == 0 and manual_count == 0
    delta_status = "no_new_evidence" if no_new else "new_evidence_detected"
    revalidation_required = not no_new
    new_rows: list[dict[str, Any]] = []
    if revalidation_required:
        new_rows.append({
            "evidence_id": "delta_check_placeholder",
            "variable": "evidence_quality",
            "source_type": "audit_check",
            "quality_bucket": "check_pending",
            "allowed_usage": "supporting_evidence",
        })
    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "new_evidence_delta": {
            "new_evidence_found": revalidation_required,
            "new_candidates_found": manual_count > 0,
            "evidence_count_before": evidence_count,
            "evidence_count_after": evidence_count,
            "manual_candidates_count": manual_count,
            "new_evidence_rows": new_rows,
            "delta_status": delta_status,
            "revalidation_required": revalidation_required,
        },
        "safety": {
            "delta_does_not_fetch_raw": True,
            "delta_does_not_pending": True,
            "delta_does_not_order": True,
            "pending_created": 0,
            "paper_order_created": 0,
            "real_trade_created": 0,
        },
    }
