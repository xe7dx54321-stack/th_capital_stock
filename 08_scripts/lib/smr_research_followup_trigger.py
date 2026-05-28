#!/usr/bin/env python3
"""Detect Phase 41 research follow-up triggers from Phase 40 state."""

from __future__ import annotations

import sqlite3
from collections import Counter
from typing import Any

from smr_research_review_audit import list_audit_records
from smr_research_review_lifecycle import (
    REPAIR_ONLY_TICKER,
    TARGET_REVIEW_TICKER,
    build_phase39_lifecycle_object,
    get_lifecycle_by_ticker,
    normalize_ticker,
)
from smr_wiki import now_ts


FOLLOWUP_TRIGGER_STATUSES = {
    "reviewed_request_deeper_research",
    "reviewed_request_specific_evidence",
    "reviewed_continue_evidence",
}

TRIGGER_NEXT_STEPS = {
    "reviewed_request_deeper_research": "generate_specific_evidence_followup_tasks",
    "reviewed_request_specific_evidence": "execute_specific_evidence_request",
    "reviewed_continue_evidence": "continue_evidence_acquisition_plan",
}


def _phase40_audits_for_trigger(conn: sqlite3.Connection, ticker: str, trigger_status: str) -> list[dict[str, Any]]:
    action_by_status = {
        "reviewed_request_deeper_research": "request_deeper_research",
        "reviewed_request_specific_evidence": "request_specific_evidence",
        "reviewed_continue_evidence": "continue_evidence_acquisition",
    }
    action = action_by_status.get(trigger_status)
    return [
        row
        for row in list_audit_records(conn, ticker=ticker, limit=200)
        if row.get("after_status") == trigger_status or row.get("action") == action
    ]


def _trigger_row(conn: sqlite3.Connection, ticker: str) -> dict[str, Any] | None:
    lifecycle = get_lifecycle_by_ticker(conn, ticker)
    if not lifecycle and normalize_ticker(ticker) == TARGET_REVIEW_TICKER:
        lifecycle = build_phase39_lifecycle_object(conn, ticker)
    status = str((lifecycle or {}).get("research_review_status") or "unknown")
    if status not in FOLLOWUP_TRIGGER_STATUSES:
        return None
    audits = _phase40_audits_for_trigger(conn, ticker, status)
    return {
        "ticker": normalize_ticker(ticker),
        "trigger_type": status,
        "source_phase": "phase40",
        "audit_records": len(audits),
        "trigger_status": "active" if audits else "missing_execute_audit",
        "next_step": TRIGGER_NEXT_STEPS.get(status, "review_manually"),
        "notes": [] if audits else ["execute action audit is missing; lifecycle still indicates follow-up is needed"],
    }


def build_followup_trigger_summary(conn: sqlite3.Connection, ticker: str | None = None) -> dict[str, Any]:
    ticker_filter = normalize_ticker(ticker) if ticker else None
    tickers = [ticker_filter] if ticker_filter else [TARGET_REVIEW_TICKER, REPAIR_ONLY_TICKER]
    trigger_rows: list[dict[str, Any]] = []
    excluded_rows: list[dict[str, Any]] = []
    for item in tickers:
        if item == REPAIR_ONLY_TICKER:
            excluded_rows.append({"ticker": item, "reason": "repair_required_before_review"})
            continue
        row = _trigger_row(conn, item)
        if row:
            trigger_rows.append(row)
        else:
            excluded_rows.append({"ticker": item, "reason": "no_active_followup_trigger"})
    counts = Counter(row.get("trigger_type") for row in trigger_rows)
    return {
        "generated_at": now_ts(),
        "summary": {
            "tickers_checked": len(tickers),
            "followup_triggers_found": len(trigger_rows),
            "request_deeper_research": counts.get("reviewed_request_deeper_research", 0),
            "request_specific_evidence": counts.get("reviewed_request_specific_evidence", 0),
            "continue_evidence_acquisition": counts.get("reviewed_continue_evidence", 0),
            "repair_required_excluded": sum(1 for row in excluded_rows if row.get("reason") == "repair_required_before_review"),
            "pending_created": 0,
            "paper_order_created": 0,
        },
        "trigger_rows": trigger_rows,
        "excluded_rows": excluded_rows,
        "safety": {
            "investment_conclusion_generated": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_rules_relaxed": False,
        },
    }
